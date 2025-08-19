from pathlib import Path

import pytest

from ..exceptions import FastBundleLoaderUnknownFactoryNameError, FastIncompatibleServiceClassError
from ..service_registry import RegisterSpecializedService

DATA_FOLDER_PATH = Path(__file__).parent / "data"


# Initialization of services ###############
class DummyBase:
    def my_class(self):
        return self.__class__.__name__


class RegisterDummyServiceA(RegisterSpecializedService, base_class=DummyBase):
    pass


class RegisterDummyServiceB(
    RegisterSpecializedService, base_class=DummyBase, service_id="dummy.service.B"
):
    pass


# Tests ####################################
@pytest.fixture(scope="module")
def load():
    """Loads components"""
    RegisterSpecializedService.explore_folder(DATA_FOLDER_PATH / "dummy_services")


def test_get_provider_ids_without_explore_folders():
    assert RegisterDummyServiceA.get_provider_ids() == []
    assert RegisterDummyServiceB.get_provider_ids() == []


def test_register(load):
    assert (
        RegisterDummyServiceA.service_id
        == "fastoad.module_management.service_registry.RegisterDummyServiceA"
    )
    assert RegisterDummyServiceB.service_id == "dummy.service.B"

    # Tests error if base class is not respected
    class TooDummy:
        pass

    with pytest.raises(FastIncompatibleServiceClassError):
        RegisterDummyServiceA("too.dummy")(TooDummy)

    # Registering without error is done in data/dummy_service.py


def test_get_provider_ids(load):
    assert RegisterDummyServiceA.get_provider_ids() == ["dummy.provider.1", "dummy.provider.2"]
    assert RegisterDummyServiceB.get_provider_ids() == []


def test_get_provider(load):
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        _ = RegisterDummyServiceA.get_provider("dummy.provider.0")

    my_dummy1: DummyBase = RegisterDummyServiceA.get_provider("dummy.provider.1")
    assert my_dummy1.my_class() == "Dummy1"

    my_dummy2: DummyBase = RegisterDummyServiceA.get_provider("dummy.provider.2")
    assert my_dummy2.my_class() == "Dummy2"
