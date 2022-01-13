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

from fastoad.openmdao.variables import Variable
from .._plugins import FastoadLoader
from ..exceptions import FastBundleLoaderUnknownFactoryNameError
from ..service_registry import RegisterService

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


# Tests ####################################
def test_plugins(with_dummy_plugins):

    FastoadLoader._loaded = True  # Ensures next instantiation will NOT trigger reloading

    # Before FastoadLoader.load(), services are not registered
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        declared_dummy_1 = RegisterService.get_provider("test.plugin.declared.1")
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        decorated_dummy_1 = RegisterService.get_provider("test.plugin.decorated.1")

    FastoadLoader._loaded = False  # Ensures next instantiation will trigger reloading

    plugin1_definition = FastoadLoader().plugin_definitions["dummy-dist-1"]
    assert "models" not in plugin1_definition["test_plugin_1"].subpackages
    assert "notebooks" not in plugin1_definition["test_plugin_1"].subpackages

    plugin4_definition = FastoadLoader().plugin_definitions["dummy-dist-1"]
    assert "models" not in plugin4_definition["test_plugin_4"].subpackages
    assert "configurations" not in plugin4_definition["test_plugin_4"].subpackages

    plugin3_definition = FastoadLoader().plugin_definitions["dummy-dist-2"]
    assert (
        plugin3_definition["test_plugin_3"].subpackages["models"]
        == "tests.dummy_plugins.dist_2.dummy_plugin_3.models"
    )
    assert (
        plugin3_definition["test_plugin_3"].subpackages["notebooks"]
        == "tests.dummy_plugins.dist_2.dummy_plugin_3.notebooks"
    )
    assert (
        plugin3_definition["test_plugin_3"].subpackages["configurations"]
        == "tests.dummy_plugins.dist_2.dummy_plugin_3.configurations"
    )

    declared_dummy_1 = RegisterService.get_provider("test.plugin.declared.1")
    assert declared_dummy_1.my_class() == "DeclaredDummy1"
    declared_dummy_2 = RegisterService.get_provider("test.plugin.declared.2")
    assert declared_dummy_2.my_class() == "DeclaredDummy2"

    decorated_dummy_1 = RegisterService.get_provider("test.plugin.decorated.1")
    assert decorated_dummy_1.my_class() == "DecoratedDummy1"
    decorated_dummy_2 = RegisterService.get_provider("test.plugin.decorated.2")
    assert decorated_dummy_2.my_class() == "DecoratedDummy2"
    # This one is in a subpackage
    decorated_dummy_3 = RegisterService.get_provider("test.plugin.decorated.3")
    assert decorated_dummy_3.my_class() == "DecoratedDummy3"

    # Checking variable description.
    assert Variable("dummy:variable").description == "Some dummy variable."


def test_get_plugin_configuration_file_list(with_dummy_plugins):
    def extract_info(file_list):
        return {(item.file_name, item.plugin_name) for item in file_list}

    file_list = FastoadLoader().get_configuration_file_list("dummy-dist-1")
    assert extract_info(file_list) == {("dummy_conf_1-1.yml", "test_plugin_1")}
    file_list = FastoadLoader().get_configuration_file_list("dummy-dist-1", "test_plugin_1")
    assert extract_info(file_list) == {("dummy_conf_1-1.yml", "test_plugin_1")}
    file_list = FastoadLoader().get_configuration_file_list("dummy-dist-1", "test_plugin_4")
    assert extract_info(file_list) == set()

    file_list = FastoadLoader().get_configuration_file_list("dummy-dist-2")
    assert extract_info(file_list) == {
        ("dummy_conf_2-1.yml", "test_plugin_2"),
        ("dummy_conf_3-1.yml", "test_plugin_3"),
        ("dummy_conf_3-2.yaml", "test_plugin_3"),
    }
    file_list = FastoadLoader().get_configuration_file_list("dummy-dist-2", "test_plugin_2")
    assert extract_info(file_list) == {("dummy_conf_2-1.yml", "test_plugin_2")}
    file_list = FastoadLoader().get_configuration_file_list("dummy-dist-2", "test_plugin_3")
    assert extract_info(file_list) == {
        ("dummy_conf_3-1.yml", "test_plugin_3"),
        ("dummy_conf_3-2.yaml", "test_plugin_3"),
    }

    # improper names
    file_list = FastoadLoader().get_configuration_file_list("unknown-dist-1")
    assert extract_info(file_list) == set()
    file_list = FastoadLoader().get_configuration_file_list("dummy-dist-1", "unknown_plugin")
    assert extract_info(file_list) == set()
