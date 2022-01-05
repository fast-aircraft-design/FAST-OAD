#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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
from pkg_resources import EntryPoint, get_distribution

from .._plugins import FastoadLoader, MODEL_PLUGIN_ID
from ..exceptions import FastBundleLoaderUnknownFactoryNameError
from ..service_registry import RegisterSpecializedService
from ...openmdao.variables import Variable

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


# Initialization of services ###############
class DummyBase:
    def my_class(self):
        return self.__class__.__name__


class RegisterDummyService(RegisterSpecializedService, base_class=DummyBase):
    pass


@pytest.fixture
def dummy_plugin_declaration():
    # Declaring the plugin
    dist = get_distribution("FAST-OAD")

    original_entry_map = dist.get_entry_map(MODEL_PLUGIN_ID).copy()
    entry_map = dist.get_entry_map(MODEL_PLUGIN_ID)
    entry_map["test_plugin"] = EntryPoint(
        "test_plugin",
        "fastoad.module_management.tests.data.dummy_plugin",
        dist=dist,
    )

    # Ensure next instantiation of FastoadLoader will trigger reloading plugins
    FastoadLoader._loaded = False

    yield

    # cleaning
    entry_map.clear()
    entry_map.update(original_entry_map)
    FastoadLoader._loaded = False


# Tests ####################################
def test_plugins(dummy_plugin_declaration):

    FastoadLoader._loaded = True  # Ensures next instantiation will NOT trigger reloading

    # Before FastoadLoader.load(), services are not registered
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        declared_dummy_1 = RegisterDummyService.get_provider("test.plugin.declared.1")
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        decorated_dummy_1 = RegisterDummyService.get_provider("test.plugin.decorated.1")

    FastoadLoader._loaded = False  # Ensures next instantiation will trigger reloading

    assert (
        FastoadLoader().plugin_definitions["test_plugin"].subpackages["models"]
        == "fastoad.module_management.tests.data.dummy_plugin.models"
    )
    assert (
        FastoadLoader().plugin_definitions["test_plugin"].subpackages["notebooks"]
        == "fastoad.module_management.tests.data.dummy_plugin.notebooks"
    )
    assert (
        FastoadLoader().plugin_definitions["test_plugin"].subpackages["configurations"]
        == "fastoad.module_management.tests.data.dummy_plugin.configurations"
    )

    declared_dummy_1 = RegisterDummyService.get_provider("test.plugin.declared.1")
    assert declared_dummy_1.my_class() == "DeclaredDummy1"
    declared_dummy_2 = RegisterDummyService.get_provider("test.plugin.declared.2")
    assert declared_dummy_2.my_class() == "DeclaredDummy2"

    decorated_dummy_1 = RegisterDummyService.get_provider("test.plugin.decorated.1")
    assert decorated_dummy_1.my_class() == "DecoratedDummy1"
    decorated_dummy_2 = RegisterDummyService.get_provider("test.plugin.decorated.2")
    assert decorated_dummy_2.my_class() == "DecoratedDummy2"
    # This one is in a subpackage
    decorated_dummy_3 = RegisterDummyService.get_provider("test.plugin.decorated.3")
    assert decorated_dummy_3.my_class() == "DecoratedDummy3"

    # Checking variable description.
    assert Variable("dummy:variable").description == "Some dummy variable."


def test_get_configuration_file_list(dummy_plugin_declaration):
    file_list = FastoadLoader().get_configuration_file_list()
    assert set(file_list.keys()) == {"cs25", "test_plugin"}
    assert set(file_list["test_plugin"]) == {"dummy_conf_1.yml", "dummy_conf_2.yaml"}
