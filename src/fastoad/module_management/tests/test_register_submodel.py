from pathlib import Path

import pytest

from .._bundle_loader import BundleLoader
from ..exceptions import (
    FastBundleLoaderUnavailableFactoryError,
    FastNoSubmodelFoundError,
    FastTooManySubmodelsError,
    FastUnknownSubmodelError,
)
from ..service_registry import RegisterSubmodel

DATA_FOLDER_PATH = Path(__file__).parent / "data"


# Tests ####################################
@pytest.fixture(scope="module")
def load():
    """Loads components"""
    previous_active_submodels = RegisterSubmodel.active_models
    RegisterSubmodel.active_models = {}
    BundleLoader().explore_folder(DATA_FOLDER_PATH / "dummy_submodels")
    yield
    RegisterSubmodel.active_models = previous_active_submodels


def test_get_submodel_unknown_identifier(load):
    with pytest.raises(FastNoSubmodelFoundError):
        _ = RegisterSubmodel.get_submodel("requirement.0")


def test_get_submodel_one_match(load):
    obj = RegisterSubmodel.get_submodel("requirement.1")
    assert obj.__class__.__name__ == "UniqueSubmodelForRequirement1"


def test_get_submodel_several_matches(load):
    with pytest.raises(FastTooManySubmodelsError):
        _ = RegisterSubmodel.get_submodel("requirement.2")

    RegisterSubmodel.active_models["requirement.2"] = "req.1.submodel"
    with pytest.raises(FastUnknownSubmodelError):
        _ = RegisterSubmodel.get_submodel("requirement.2")

    RegisterSubmodel.active_models["requirement.2"] = "req.2.submodel.A"
    obj = RegisterSubmodel.get_submodel("requirement.2")
    assert obj.__class__.__name__ == "SubmodelAForRequirement2"

    RegisterSubmodel.active_models["requirement.2"] = "req.2.submodel.B"
    obj = RegisterSubmodel.get_submodel("requirement.2")
    assert obj.__class__.__name__ == "SubmodelBForRequirement2"


def test_get_submodel_deactivation(load):
    RegisterSubmodel.active_models["requirement.1"] = None
    obj = RegisterSubmodel.get_submodel("requirement.1")
    assert obj.__class__.__name__ == "Group"

    RegisterSubmodel.active_models["requirement.1"] = ""
    obj = RegisterSubmodel.get_submodel("requirement.1")
    assert obj.__class__.__name__ == "Group"

    RegisterSubmodel.active_models["requirement.2"] = None
    obj = RegisterSubmodel.get_submodel("requirement.2")
    assert obj.__class__.__name__ == "Group"

    # Now we cancel deactivation
    RegisterSubmodel.cancel_submodel_deactivations()
    obj = RegisterSubmodel.get_submodel("requirement.1")
    assert obj.__class__.__name__ == "UniqueSubmodelForRequirement1"

    with pytest.raises(FastTooManySubmodelsError):
        _ = RegisterSubmodel.get_submodel("requirement.2")


def test_unavailable_submodel(load):
    """
    Tests the mechanism for unavailable submodel. Unavailable submodel are submodels that are
    recognized but not expected to be usable unless certain conditions are met, for instance they
    won't work unless some optional dependencies are installed. It should raise a different error
    than when the submodel is not recognized.
    """
    # This model exists AND is available
    RegisterSubmodel.active_models["requirement.2"] = "req.2.submodel.B"
    _ = RegisterSubmodel.get_submodel("requirement.2")

    # This model exists, but is unavailable
    assert "req.2.submodel.C" in BundleLoader().get_factory_names("requirement.2")

    RegisterSubmodel.active_models["requirement.2"] = "req.2.submodel.C"

    with pytest.raises(FastBundleLoaderUnavailableFactoryError):
        _ = RegisterSubmodel.get_submodel("requirement.2")
