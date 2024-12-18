#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

import pytest

from fastoad.openmdao.variables import Variable

from .._plugins import FastoadLoader, SubPackageNames
from ..exceptions import (
    FastBundleLoaderUnknownFactoryNameError,
    FastNoAvailableConfigurationFileError,
    FastNoAvailableSourceDataFileError,
    FastNoDistPluginError,
    FastSeveralConfigurationFilesError,
    FastSeveralDistPluginsError,
    FastSeveralSourceDataFilesError,
    FastUnknownConfigurationFileError,
    FastUnknownDistPluginError,
    FastUnknownSourceDataFileError,
)
from ..service_registry import RegisterService


# Tests ####################################
def test_plugins(with_dummy_plugins):
    FastoadLoader._loaded = True  # Ensures next instantiation will NOT trigger reloading

    # Before FastoadLoader.load(), services are not registered
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        declared_dummy_1 = RegisterService.get_provider("test.plugin.declared.1")
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        decorated_dummy_1 = RegisterService.get_provider("test.plugin.decorated.1")

    FastoadLoader._loaded = False  # Ensures next instantiation will trigger reloading

    dist1_definition = FastoadLoader().distribution_plugin_definitions["dummy-dist-1"]
    assert SubPackageNames.MODELS not in dist1_definition["test_plugin_1"].subpackages
    assert (
        dist1_definition["test_plugin_1"].subpackages[SubPackageNames.NOTEBOOKS]
        == "tests.dummy_plugins.dist_1.dummy_plugin_1.notebooks"
    )
    assert SubPackageNames.SOURCE_DATA_FILES not in dist1_definition["test_plugin_1"].subpackages

    assert SubPackageNames.MODELS not in dist1_definition["test_plugin_4"].subpackages
    assert SubPackageNames.CONFIGURATIONS not in dist1_definition["test_plugin_4"].subpackages
    assert (
        dist1_definition["test_plugin_4"].subpackages[SubPackageNames.SOURCE_DATA_FILES]
        == "tests.dummy_plugins.dist_1.dummy_plugin_4.source_data_files"
    )

    dist2_definition = FastoadLoader().distribution_plugin_definitions["dummy-dist-2"]
    assert (
        dist2_definition["test_plugin_3"].subpackages[SubPackageNames.MODELS]
        == "tests.dummy_plugins.dist_2.dummy_plugin_3.models"
    )
    assert SubPackageNames.NOTEBOOKS not in dist2_definition["test_plugin_3"].subpackages
    assert (
        dist2_definition["test_plugin_3"].subpackages[SubPackageNames.CONFIGURATIONS]
        == "tests.dummy_plugins.dist_2.dummy_plugin_3.configurations"
    )
    assert (
        dist2_definition["test_plugin_3"].subpackages[SubPackageNames.SOURCE_DATA_FILES]
        == "tests.dummy_plugins.dist_2.dummy_plugin_3.source_data_files"
    )

    dist3_definition = FastoadLoader().distribution_plugin_definitions["dummy-dist-3"]
    assert SubPackageNames.SOURCE_DATA_FILES not in dist3_definition["test_plugin_5"].subpackages

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


def test_get_distribution_plugin_definition_with_0_plugin(with_no_plugin):
    with pytest.raises(FastNoDistPluginError):
        FastoadLoader().get_distribution_plugin_definition()
    with pytest.raises(FastNoDistPluginError):
        FastoadLoader().get_distribution_plugin_definition("anything")


def test_get_distribution_plugin_definition_with_1_plugin(with_dummy_plugin_1):
    with pytest.raises(FastUnknownDistPluginError):
        FastoadLoader().get_distribution_plugin_definition("unknown")

    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-1")
    assert dist_def.dist_name == "dummy-dist-1"
    assert set(dist_def.keys()) == {"test_plugin_1"}
    assert dist_def["test_plugin_1"].package_name == "tests.dummy_plugins.dist_1.dummy_plugin_1"

    dist_def_bis = FastoadLoader().get_distribution_plugin_definition()
    assert dist_def == dist_def_bis


def test_get_distribution_plugin_definition_with_plugins(with_dummy_plugins):
    with pytest.raises(FastSeveralDistPluginsError):
        FastoadLoader().get_distribution_plugin_definition()
    with pytest.raises(FastUnknownDistPluginError):
        FastoadLoader().get_distribution_plugin_definition("unknown")

    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-1")
    assert dist_def.dist_name == "dummy-dist-1"
    assert set(dist_def.keys()) == {"test_plugin_1", "test_plugin_4"}
    assert dist_def["test_plugin_1"].package_name == "tests.dummy_plugins.dist_1.dummy_plugin_1"
    assert dist_def["test_plugin_4"].package_name == "tests.dummy_plugins.dist_1.dummy_plugin_4"

    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-2")
    assert dist_def.dist_name == "dummy-dist-2"
    assert set(dist_def.keys()) == {"test_plugin_2", "test_plugin_3"}
    assert dist_def["test_plugin_2"].package_name == "tests.dummy_plugins.dist_2.dummy_plugin_2"
    assert dist_def["test_plugin_3"].package_name == "tests.dummy_plugins.dist_2.dummy_plugin_3"


def test_get_plugin_configuration_file_list(with_dummy_plugins):
    def extract_info(file_list):
        return {(item.name, item.plugin_name) for item in file_list}

    # Provided distribution name is intentionally upper case with underscores.
    # Should be treated as "dummy-dist-1".
    file_list = FastoadLoader().get_configuration_file_list("DUMMY_DIST_1")
    assert extract_info(file_list) == {("dummy_conf_1-1.yml", "test_plugin_1")}

    file_list = FastoadLoader().get_configuration_file_list("dummy-dist-2")
    assert extract_info(file_list) == {
        ("dummy_conf_2-1.yml", "test_plugin_2"),
        ("dummy_conf_3-1.yml", "test_plugin_3"),
        ("dummy_conf_3-2.yaml", "test_plugin_3"),
    }

    file_list = FastoadLoader().get_configuration_file_list("dummy-dist-3")
    assert extract_info(file_list) == set()

    # improper name
    with pytest.raises(FastUnknownDistPluginError):
        file_list = FastoadLoader().get_configuration_file_list("unknown-dist")


def test_get_plugin_source_data_file_list(with_dummy_plugins):
    def extract_info(file_list):
        return {(item.name, item.plugin_name) for item in file_list}

    # Provided distribution name is intentionally upper case with underscores.
    # Should be treated as "dummy-dist-1".
    file_list = FastoadLoader().get_source_data_file_list("DUMMY_DIST-1")
    assert extract_info(file_list) == {("dummy_source_data_4-1.xml", "test_plugin_4")}

    file_list = FastoadLoader().get_source_data_file_list("dummy-dist-2")
    assert extract_info(file_list) == {
        ("dummy_source_data_3-1.xml", "test_plugin_3"),
        ("dummy_source_data_3-2.xml", "test_plugin_3"),
        ("dummy_source_data_3-3.xml", "test_plugin_3"),
    }

    file_list = FastoadLoader().get_source_data_file_list("dummy-dist-3")
    assert extract_info(file_list) == set()

    # improper name
    with pytest.raises(FastUnknownDistPluginError):
        file_list = FastoadLoader().get_configuration_file_list("unknown-dist")


def test_get_plugin_notebook_folder_list_with_one_plugin(with_dummy_plugin_distribution_1):
    def extract_info(folder_list):
        return {(item.dist_name, item.package_name) for item in folder_list}

    folder_list = FastoadLoader().get_notebook_folder_list()
    assert extract_info(folder_list) == {
        ("dummy-dist-1", "tests.dummy_plugins.dist_1.dummy_plugin_1.notebooks"),
        ("dummy-dist-1", "tests.dummy_plugins.dist_1.dummy_plugin_4.notebooks"),
    }
    folder_list = FastoadLoader().get_notebook_folder_list("dummy-dist-1")
    assert extract_info(folder_list) == {
        ("dummy-dist-1", "tests.dummy_plugins.dist_1.dummy_plugin_1.notebooks"),
        ("dummy-dist-1", "tests.dummy_plugins.dist_1.dummy_plugin_4.notebooks"),
    }
    # improper name
    with pytest.raises(FastUnknownDistPluginError):
        _ = FastoadLoader().get_notebook_folder_list("unknown-dist")


def test_get_plugin_notebook_folder_list_with_plugins(with_dummy_plugins):
    def extract_info(folder_list):
        return {(item.dist_name, item.package_name) for item in folder_list}

    folder_list = FastoadLoader().get_notebook_folder_list()
    assert extract_info(folder_list) == {
        ("dummy-dist-1", "tests.dummy_plugins.dist_1.dummy_plugin_1.notebooks"),
        ("dummy-dist-1", "tests.dummy_plugins.dist_1.dummy_plugin_4.notebooks"),
        ("dummy-dist-3", "tests.dummy_plugins.dist_3.dummy_plugin_5.notebooks"),
    }
    # Provided distribution name is intentionally upper case with underscores.
    # Should be treated as "dummy-dist-1".
    folder_list = FastoadLoader().get_notebook_folder_list("DUMMY-dist_1")
    assert extract_info(folder_list) == {
        ("dummy-dist-1", "tests.dummy_plugins.dist_1.dummy_plugin_1.notebooks"),
        ("dummy-dist-1", "tests.dummy_plugins.dist_1.dummy_plugin_4.notebooks"),
    }
    folder_list = FastoadLoader().get_notebook_folder_list("dummy-dist-2")
    assert extract_info(folder_list) == set()
    folder_list = FastoadLoader().get_notebook_folder_list("dummy-dist-3")
    assert extract_info(folder_list) == {
        ("dummy-dist-3", "tests.dummy_plugins.dist_3.dummy_plugin_5.notebooks")
    }

    # improper name
    with pytest.raises(FastUnknownDistPluginError):
        _ = FastoadLoader().get_notebook_folder_list("unknown-dist")


def test_get_configuration_file_info_with_1_plugin(with_dummy_plugin_1):
    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-1")

    with pytest.raises(FastUnknownConfigurationFileError):
        dist_def.get_configuration_file_info("unknown.yml")
    file_info = dist_def.get_configuration_file_info("dummy_conf_1-1.yml")
    assert file_info.name == "dummy_conf_1-1.yml"
    assert file_info.dist_name == "dummy-dist-1"
    assert file_info.plugin_name == "test_plugin_1"
    assert file_info.package_name == "tests.dummy_plugins.dist_1.dummy_plugin_1.configurations"

    file_info_bis = dist_def.get_configuration_file_info()
    assert file_info_bis == file_info


def test_get_configuration_file_info_without_conf_file_available(with_dummy_plugin_4):
    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-1")

    with pytest.raises(FastNoAvailableConfigurationFileError):
        dist_def.get_configuration_file_info("unknown.yml")


def test_get_configuration_file_info_with_plugins(with_dummy_plugins):
    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-1")

    with pytest.raises(FastUnknownConfigurationFileError):
        dist_def.get_configuration_file_info("unknown.yml")
    file_info = dist_def.get_configuration_file_info("dummy_conf_1-1.yml")
    assert file_info.name == "dummy_conf_1-1.yml"
    assert file_info.dist_name == "dummy-dist-1"
    assert file_info.plugin_name == "test_plugin_1"
    assert file_info.package_name == "tests.dummy_plugins.dist_1.dummy_plugin_1.configurations"

    file_info_bis = dist_def.get_configuration_file_info()
    assert file_info_bis == file_info

    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-2")
    with pytest.raises(FastUnknownConfigurationFileError):
        dist_def.get_configuration_file_info("unknown.yml")
    with pytest.raises(FastSeveralConfigurationFilesError):
        dist_def.get_configuration_file_info()

    file_info = dist_def.get_configuration_file_info("dummy_conf_2-1.yml")
    assert file_info.name == "dummy_conf_2-1.yml"
    assert file_info.dist_name == "dummy-dist-2"
    assert file_info.plugin_name == "test_plugin_2"
    assert file_info.package_name == "tests.dummy_plugins.dist_2.dummy_plugin_2.configurations"

    file_info = dist_def.get_configuration_file_info("dummy_conf_3-1.yml")
    assert file_info.name == "dummy_conf_3-1.yml"
    assert file_info.dist_name == "dummy-dist-2"
    assert file_info.plugin_name == "test_plugin_3"
    assert file_info.package_name == "tests.dummy_plugins.dist_2.dummy_plugin_3.configurations"

    file_info = dist_def.get_configuration_file_info("dummy_conf_3-2.yaml")
    assert file_info.name == "dummy_conf_3-2.yaml"
    assert file_info.dist_name == "dummy-dist-2"
    assert file_info.plugin_name == "test_plugin_3"
    assert file_info.package_name == "tests.dummy_plugins.dist_2.dummy_plugin_3.configurations"


def test_get_source_data_file_info_with_1_plugin(with_dummy_plugin_4):
    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-1")

    with pytest.raises(FastUnknownSourceDataFileError):
        dist_def.get_source_data_file_info("unknown.xml")
    file_info = dist_def.get_source_data_file_info("dummy_source_data_4-1.xml")
    assert file_info.name == "dummy_source_data_4-1.xml"
    assert file_info.dist_name == "dummy-dist-1"
    assert file_info.plugin_name == "test_plugin_4"
    assert file_info.package_name == "tests.dummy_plugins.dist_1.dummy_plugin_4.source_data_files"

    file_info_bis = dist_def.get_source_data_file_info()
    assert file_info_bis == file_info


def test_get_source_data_file_info_without_source_data_file_available(with_dummy_plugin_2):
    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-2")

    with pytest.raises(FastNoAvailableSourceDataFileError):
        dist_def.get_source_data_file_info("unknown.xml")


def test_get_source_data_file_info_with_plugins(with_dummy_plugins):
    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-1")

    with pytest.raises(FastUnknownSourceDataFileError):
        dist_def.get_source_data_file_info("unknown.xml")
    file_info = dist_def.get_source_data_file_info("dummy_source_data_4-1.xml")
    assert file_info.name == "dummy_source_data_4-1.xml"
    assert file_info.dist_name == "dummy-dist-1"
    assert file_info.plugin_name == "test_plugin_4"
    assert file_info.package_name == "tests.dummy_plugins.dist_1.dummy_plugin_4.source_data_files"

    file_info_bis = dist_def.get_source_data_file_info()
    assert file_info_bis == file_info

    dist_def = FastoadLoader().get_distribution_plugin_definition("dummy-dist-2")
    with pytest.raises(FastUnknownSourceDataFileError):
        dist_def.get_source_data_file_info("unknown.xml")
    with pytest.raises(FastSeveralSourceDataFilesError):
        dist_def.get_source_data_file_info()

    file_info = dist_def.get_source_data_file_info("dummy_source_data_3-1.xml")
    assert file_info.name == "dummy_source_data_3-1.xml"
    assert file_info.dist_name == "dummy-dist-2"
    assert file_info.plugin_name == "test_plugin_3"
    assert file_info.package_name == "tests.dummy_plugins.dist_2.dummy_plugin_3.source_data_files"

    file_info = dist_def.get_source_data_file_info("dummy_source_data_3-2.xml")
    assert file_info.name == "dummy_source_data_3-2.xml"
    assert file_info.dist_name == "dummy-dist-2"
    assert file_info.plugin_name == "test_plugin_3"
    assert file_info.package_name == "tests.dummy_plugins.dist_2.dummy_plugin_3.source_data_files"

    file_info = dist_def.get_source_data_file_info("dummy_source_data_3-3.xml")
    assert file_info.name == "dummy_source_data_3-3.xml"
    assert file_info.dist_name == "dummy-dist-2"
    assert file_info.plugin_name == "test_plugin_3"
    assert file_info.package_name == "tests.dummy_plugins.dist_2.dummy_plugin_3.source_data_files"
