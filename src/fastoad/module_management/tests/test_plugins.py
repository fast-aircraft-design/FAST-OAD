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


# Tests ####################################
def test_plugins():
    # Declaring the plugin
    dist = get_distribution("FAST-OAD")
    dist.get_entry_map(MODEL_PLUGIN_ID)["test_plugin"] = EntryPoint(
        "test_plugin",
        "fastoad.module_management.tests.data.dummy_plugin.models",
        dist=dist,
    )
    dist.get_entry_map(MODEL_PLUGIN_ID)["test_plugin.notebooks"] = EntryPoint(
        "test_plugin.notebooks",
        "fastoad.module_management.tests.data.dummy_plugin.notebooks",
        dist=dist,
    )
    dist.get_entry_map(MODEL_PLUGIN_ID)["test_plugin.configurations"] = EntryPoint(
        "test_plugin.configurations",
        "fastoad.module_management.tests.data.dummy_plugin.confs",
        dist=dist,
    )

    # Before load_plugins(), services are not registered
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        declared_dummy_1 = RegisterDummyService.get_provider("test.plugin.declared.1")
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        decorated_dummy_1 = RegisterDummyService.get_provider("test.plugin.decorated.1")

    FastoadLoader._loaded = False  # Ensures first instantiation will trigger reloading

    assert (
        FastoadLoader().plugin_definitions["test_plugin"].module_package_name
        == "fastoad.module_management.tests.data.dummy_plugin.models"
    )
    assert (
        FastoadLoader().plugin_definitions["test_plugin"].notebook_package_name
        == "fastoad.module_management.tests.data.dummy_plugin.notebooks"
    )
    assert (
        FastoadLoader().plugin_definitions["test_plugin"].conf_file_package_name
        == "fastoad.module_management.tests.data.dummy_plugin.confs"
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
