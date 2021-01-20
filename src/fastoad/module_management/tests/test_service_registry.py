#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

from fastoad.module_management.exceptions import (
    FastBundleLoaderUnknownFactoryNameError,
    FastIncompatibleServiceClassError,
)
from fastoad.module_management.service_registry import RegisterService

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


# Initialization of services ###############
class DummyBase:
    def my_class(self):
        return self.__class__.__name__


class RegisterDummyServiceA(RegisterService, base_class=DummyBase):
    pass


class RegisterDummyServiceB(RegisterService, base_class=DummyBase, service_id="dummy.service.B"):
    pass


# Tests ####################################
@pytest.fixture(scope="module")
def load():
    """ Loads components """
    RegisterService.explore_folder(pth.join(DATA_FOLDER_PATH, "dummy_services"))


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
        my_dummy0 = RegisterDummyServiceA.get_provider("dummy.provider.0")

    my_dummy1: DummyBase = RegisterDummyServiceA.get_provider("dummy.provider.1")
    assert my_dummy1.my_class() == "Dummy1"

    my_dummy2: DummyBase = RegisterDummyServiceA.get_provider("dummy.provider.2")
    assert my_dummy2.my_class() == "Dummy2"
