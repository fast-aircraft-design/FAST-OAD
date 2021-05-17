#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os.path as pth

import pytest

from .._bundle_loader import BundleLoader
from ..exceptions import (
    FastTooManySubmodelsError,
    FastUnknownSubmodelError,
)
from ..service_registry import RegisterSubmodel

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


# Initialization of services ###############
class RegisterRequirement1(RegisterSubmodel, service_id="requirement.1"):
    """Register a submodel that provides requirement 1"""


class RegisterRequirement2(RegisterSubmodel, service_id="requirement.2"):
    """Register a submodel that provides requirement 2"""


# Tests ####################################
@pytest.fixture(scope="module")
def load():
    """ Loads components """
    BundleLoader().explore_folder(pth.join(DATA_FOLDER_PATH, "dummy_submodels"))


def test_get_submodel_one_match(load):
    obj = RegisterRequirement1.get_submodel()
    assert obj.__class__.__name__ == "UniqueSubmodelForRequirement1"


def test_get_submodel_several_matches(load):
    with pytest.raises(FastTooManySubmodelsError):
        _ = RegisterRequirement2.get_submodel()

    RegisterSubmodel.active_models["requirement.2"] = "req.1.submodel"
    with pytest.raises(FastUnknownSubmodelError):
        _ = RegisterRequirement2.get_submodel()

    RegisterSubmodel.active_models["requirement.2"] = "req.2.submodel.A"
    obj = RegisterRequirement2.get_submodel()
    assert obj.__class__.__name__ == "SubmodelAForRequirement2"

    RegisterSubmodel.active_models["requirement.2"] = "req.2.submodel.B"
    obj = RegisterRequirement2.get_submodel()
    assert obj.__class__.__name__ == "SubmodelBForRequirement2"
