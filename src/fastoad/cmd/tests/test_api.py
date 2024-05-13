"""
Tests for basic API
"""
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

import os
import shutil
from filecmp import cmp
from pathlib import Path

import pytest

import fastoad.models
from fastoad.io import DataFile
from fastoad.openmdao.variables import Variable
from .. import api
from ..exceptions import (
    FastNoAvailableNotebookError,
    FastPathExistsError,
)

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results"
CONFIGURATION_FILE_PATH = DATA_FOLDER_PATH / "sellar.yml"


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)

    # Need to clean up variable descriptions because it is manipulated in other tests.
    Variable.read_variable_descriptions(Path(fastoad.models.__file__).parent, update_existing=False)


def test_generate_notebooks_with_no_notebook(cleanup, with_dummy_plugin_2, plugin_root_path):
    target_path = Path(RESULTS_FOLDER_PATH, "notebooks_noplugin")

    with pytest.raises(FastNoAvailableNotebookError):
        api.generate_notebooks(target_path)


def test_generate_notebooks_with_one_plugin(cleanup, with_dummy_plugin_1, plugin_root_path):
    target_path = RESULTS_FOLDER_PATH / "notebooks_1plugin"

    api.generate_notebooks(target_path)
    assert (target_path / "notebook_1.ipynb").is_file()


def test_generate_notebooks_with_one_dist_plugin(
    cleanup, with_dummy_plugin_distribution_1, plugin_root_path
):
    target_path = RESULTS_FOLDER_PATH / "notebooks_1dist"

    api.generate_notebooks(target_path)
    assert (target_path / "test_plugin_1" / "notebook_1.ipynb").is_file()
    assert (target_path / "test_plugin_4" / "notebook_1.ipynb").is_file()
    assert (target_path / "test_plugin_4" / "data").is_dir()
    assert (target_path / "test_plugin_4" / "data" / "dummy_file.txt").is_file()


def test_generate_notebooks(cleanup, with_dummy_plugins, plugin_root_path):
    target_path = RESULTS_FOLDER_PATH / "notebooks"

    # Test distribution specification
    api.generate_notebooks(target_path, distribution_name="dummy-dist-3")
    assert (target_path / "notebook_2.ipynb").is_file()

    # Test overwrite
    with pytest.raises(FastPathExistsError):
        api.generate_notebooks(target_path)

    # ... without specifying distribution
    api.generate_notebooks(target_path, overwrite=True)
    assert (target_path / "dummy-dist-1" / "test_plugin_1" / "notebook_1.ipynb").is_file()
    assert (target_path / "dummy-dist-1" / "test_plugin_4" / "notebook_1.ipynb").is_file()
    assert (target_path / "dummy-dist-1" / "test_plugin_4" / "data").is_dir()
    assert (target_path / "dummy-dist-1" / "test_plugin_4" / "data" / "dummy_file.txt").is_file()

    assert not (target_path / "dummy-dist-2").exists()

    assert (target_path / "dummy-dist-3" / "notebook_2.ipynb").is_file()


def test_generate_user_file(cleanup, with_dummy_plugins, plugin_root_path):
    # Tests that exceptions are correctly raised. The tests on other issues and on the expected
    # results will be tested with each type of user file.

    text_file_path = RESULTS_FOLDER_PATH / "unknown_user_file_type.xml"

    # Test with wrong type of user file, should fail regardless of distribution
    with pytest.raises(AttributeError):
        api._generate_user_file(
            api.UserFileType.OUTPUT_FILE,
            text_file_path,
            overwrite=False,
        )

    # Should also fail with existing and valid file but wrong choice of file type
    with pytest.raises(AttributeError):
        api._generate_user_file(
            api.UserFileType.OUTPUT_FILE,
            text_file_path,
            overwrite=False,
            distribution_name="dummy-dist-1",
        )


def test_generate_configuration_file_plugin_1(cleanup, with_dummy_plugins, plugin_root_path):
    configuration_file_path = RESULTS_FOLDER_PATH / "from_plugin_1.yml"

    # No conf file specified because the dist has only one
    api.generate_configuration_file(
        configuration_file_path, overwrite=False, distribution_name="dummy-dist-1"
    )
    original_file = Path(
        plugin_root_path, "dist_1", "dummy_plugin_1", "configurations", "dummy_conf_1-1.yml"
    )
    assert cmp(configuration_file_path, original_file)

    # Generating again without forcing overwrite will make it fail
    with pytest.raises(FastPathExistsError):
        api.generate_configuration_file(
            configuration_file_path, overwrite=False, distribution_name="dummy-dist-1"
        )

    # Generating again with overwrite=True should be Ok
    api.generate_configuration_file(
        configuration_file_path, overwrite=True, distribution_name="dummy-dist-1"
    )


def test_generate_configuration_file_plugin_1_alone(cleanup, with_dummy_plugin_1):
    configuration_file_path = RESULTS_FOLDER_PATH / "from_plugin_1.yml"

    # No plugin specified, only one plugin is available
    api.generate_configuration_file(configuration_file_path, overwrite=True)


def test_generate_configuration_file_plugin_1_and_3(
    cleanup, with_dummy_plugin_distribution_1_and_3
):
    configuration_file_path = RESULTS_FOLDER_PATH / "from_plugin_1_again.yml"

    # No plugin specified, several plugins available, but only one with a conf file
    api.generate_configuration_file(configuration_file_path, overwrite=True)


def test_generate_configuration_file_plugin_2(cleanup, with_dummy_plugins, plugin_root_path):
    configuration_file_path = RESULTS_FOLDER_PATH / "from_plugin_2.yml"
    api.generate_configuration_file(
        configuration_file_path,
        overwrite=True,
        distribution_name="dummy-dist-2",
        sample_file_name="dummy_conf_2-1.yml",
    )

    # As conf file names are unique, it is possible to omit distribution_name
    configuration_file_path = RESULTS_FOLDER_PATH / "from_plugin_2_again.yml"
    api.generate_configuration_file(
        configuration_file_path,
        overwrite=True,
        sample_file_name="dummy_conf_2-1.yml",
    )
    original_file = Path(
        plugin_root_path, "dist_2", "dummy_plugin_2", "configurations", "dummy_conf_2-1.yml"
    )
    assert cmp(configuration_file_path, original_file)

    with pytest.raises(FastPathExistsError):
        api.generate_configuration_file(
            configuration_file_path,
            overwrite=False,
            distribution_name="dummy-dist-2",
            sample_file_name="dummy_conf_3-2.yaml",
        )

    api.generate_configuration_file(
        configuration_file_path,
        overwrite=True,
        distribution_name="dummy-dist-2",
        sample_file_name="dummy_conf_3-2.yaml",
    )
    original_file = Path(
        plugin_root_path, "dist_2", "dummy_plugin_3", "configurations", "dummy_conf_3-2.yaml"
    )
    assert cmp(configuration_file_path, original_file)


def test_generate_source_data_file_plugin_4(cleanup, with_dummy_plugins, plugin_root_path):
    source_data_file_path = RESULTS_FOLDER_PATH / "from_plugin_4.xml"

    # No conf file specified because the dist has only one
    api.generate_source_data_file(
        source_data_file_path, overwrite=False, distribution_name="dummy-dist-1"
    )
    original_file = Path(
        plugin_root_path,
        "dist_1",
        "dummy_plugin_4",
        "source_data_files",
        "dummy_source_data_4-1.xml",
    )
    assert cmp(source_data_file_path, original_file)

    # Generating again without forcing overwrite will make it fail
    with pytest.raises(FastPathExistsError):
        api.generate_source_data_file(
            source_data_file_path, overwrite=False, distribution_name="dummy-dist-1"
        )

    # Generating again with overwrite=True should be Ok
    api.generate_source_data_file(
        source_data_file_path, overwrite=True, distribution_name="dummy-dist-1"
    )


def test_generate_source_data_file_plugin_4_alone(cleanup, with_dummy_plugin_4):
    source_data_file_path = RESULTS_FOLDER_PATH / "from_plugin_4.xml"

    # No plugin specified, only one plugin is available
    api.generate_source_data_file(source_data_file_path, overwrite=True)


def test_generate_source_data_file_plugin_1_and_3(cleanup, with_dummy_plugin_distribution_1_and_3):
    source_data_file_path = RESULTS_FOLDER_PATH / "from_plugin_4_again.xml"

    # No plugin specified, several plugins available, but only one with a conf file
    api.generate_source_data_file(source_data_file_path, overwrite=True)


def test_generate_source_data_file_plugin_5(cleanup, with_dummy_plugins, plugin_root_path):
    source_data_file_path = RESULTS_FOLDER_PATH / "from_plugin_3.xml"
    api.generate_source_data_file(
        source_data_file_path,
        overwrite=True,
        distribution_name="dummy-dist-2",
        sample_file_name="dummy_source_data_3-1.xml",
    )

    # As source data file names are unique, it is possible to omit distribution_name
    source_data_file_path = RESULTS_FOLDER_PATH / "from_plugin_3_again.xml"
    api.generate_source_data_file(
        source_data_file_path,
        overwrite=True,
        sample_file_name="dummy_source_data_3-1.xml",
    )
    original_file = Path(
        plugin_root_path,
        "dist_2",
        "dummy_plugin_3",
        "source_data_files",
        "dummy_source_data_3-1.xml",
    )
    assert cmp(source_data_file_path, original_file)

    with pytest.raises(FastPathExistsError):
        api.generate_source_data_file(
            source_data_file_path,
            overwrite=False,
            distribution_name="dummy-dist-2",
            sample_file_name="dummy_source_data_3-2.xml",
        )

    api.generate_source_data_file(
        source_data_file_path,
        overwrite=True,
        distribution_name="dummy-dist-2",
        sample_file_name="dummy_source_data_3-2.xml",
    )
    original_file = Path(
        plugin_root_path,
        "dist_2",
        "dummy_plugin_3",
        "source_data_files",
        "dummy_source_data_3-2.xml",
    )
    assert cmp(source_data_file_path, original_file)


def test_generate_inputs(cleanup):
    input_file_path = Path(api.generate_inputs(CONFIGURATION_FILE_PATH, overwrite=False))
    assert input_file_path == RESULTS_FOLDER_PATH / "inputs.xml"
    assert input_file_path.exists()
    data = DataFile(input_file_path)
    assert len(data) == 2
    assert "x" in data.names() and "z" in data.names()

    # Let's add another variable to ensure overwrite is correctly done (issue #328)
    data["dummy_var"] = {"value": 0.0}
    data.save()

    # Generating again without forcing overwrite will make it fail
    with pytest.raises(FastPathExistsError):
        api.generate_inputs(CONFIGURATION_FILE_PATH, overwrite=False)

    input_file_path = Path(
        api.generate_inputs(
            CONFIGURATION_FILE_PATH, DATA_FOLDER_PATH / "inputs.xml", overwrite=True
        )
    )

    assert input_file_path == RESULTS_FOLDER_PATH / "inputs.xml"
    assert input_file_path.exists()
    data = DataFile(input_file_path)
    assert len(data) == 2
    assert "x" in data.names() and "z" in data.names()

    # We test without source data file to see if variable description in "desc" kwargs
    # is captured (issue #319)
    input_file_path = Path(api.generate_inputs(CONFIGURATION_FILE_PATH, overwrite=True))
    assert input_file_path == RESULTS_FOLDER_PATH / "inputs.xml"
    assert input_file_path.exists()
    data = DataFile(input_file_path)
    assert len(data) == 2
    assert "x" in data.names() and "z" in data.names()


def test_list_modules(cleanup):
    conf_file_path = CONFIGURATION_FILE_PATH

    # Run with stdout output (no test)
    api.list_modules()
    api.list_modules(conf_file_path, verbose=True)
    api.list_modules(conf_file_path, verbose=False)

    # Run with file output (test file existence)
    out_file = RESULTS_FOLDER_PATH / "list_modules.txt"
    assert not out_file.exists()
    api.list_modules(conf_file_path, out_file)
    with pytest.raises(FastPathExistsError):
        api.list_modules(conf_file_path, out_file)
    api.list_modules(conf_file_path, out_file, overwrite=True)

    assert out_file.exists()

    #
    # Run with file output (test file existence)
    source_folder = DATA_FOLDER_PATH / "cmd_sellar_example"

    # Run with file output with folders (test file existence)
    out_file = RESULTS_FOLDER_PATH / "list_modules_with_folder.txt"
    assert not out_file.exists()
    api.list_modules(source_folder, out_file)
    with pytest.raises(FastPathExistsError):
        api.list_modules(source_folder, out_file)

    # Testing with single folder
    api.list_modules(source_folder, out_file, overwrite=True)

    assert out_file.exists()

    # Testing with list of folders
    source_folder = [source_folder]
    api.list_modules(source_folder, out_file, overwrite=True)

    assert out_file.exists()


def test_list_variables(cleanup):
    conf_file_path = CONFIGURATION_FILE_PATH

    # Run with stdout output (no test)
    api.list_variables(conf_file_path)

    # Run with file output (test file existence)
    out_file_path = RESULTS_FOLDER_PATH / "list_variables.txt"
    assert not out_file_path.exists()
    api.list_variables(conf_file_path, out=out_file_path)
    with pytest.raises(FastPathExistsError):
        api.list_variables(conf_file_path, out=out_file_path)
    api.list_variables(conf_file_path, out=out_file_path, overwrite=True)
    assert out_file_path.exists()

    ref_file_path = DATA_FOLDER_PATH / "ref_list_variables.txt"
    assert cmp(ref_file_path, out_file_path)

    # Test with variable_description.txt format
    api.list_variables(
        conf_file_path,
        out=out_file_path,
        overwrite=True,
        tablefmt="var_desc",
    )
    assert out_file_path.exists()
    ref_file_path = DATA_FOLDER_PATH.joinpath(
        "ref_list_variables_with_variable_descriptions_format.txt"
    )
    assert cmp(ref_file_path, out_file_path)


def test_write_n2(cleanup):

    n2_file_path = RESULTS_FOLDER_PATH / "other_n2.html"
    api.write_n2(CONFIGURATION_FILE_PATH, n2_file_path)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastPathExistsError):
        api.write_n2(CONFIGURATION_FILE_PATH, n2_file_path, False)
    api.write_n2(CONFIGURATION_FILE_PATH, n2_file_path, True)
    assert n2_file_path.exists()


@pytest.mark.skipif(
    str(os.environ.get("RUN_WEB_REQUESTS")).lower() not in ["true", "1", "t", "y", "yes"],
    reason="Using web access during tests should not be the default behavior.",
)
def test_write_xdsm(cleanup):
    # By default, XDSM file will be generated in same folder as configuration file
    default_xdsm_file_path = DATA_FOLDER_PATH / "xdsm.html"
    api.write_xdsm(CONFIGURATION_FILE_PATH, overwrite=True, dry_run=True)
    assert default_xdsm_file_path.exists()
    os.remove(default_xdsm_file_path)

    xdsm_file_path = RESULTS_FOLDER_PATH / "other_xdsm.html"
    api.write_xdsm(CONFIGURATION_FILE_PATH, xdsm_file_path)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastPathExistsError):
        api.write_xdsm(CONFIGURATION_FILE_PATH, xdsm_file_path, overwrite=False, dry_run=True)
    api.write_xdsm(CONFIGURATION_FILE_PATH, xdsm_file_path, overwrite=True, dry_run=True)
    assert xdsm_file_path.exists()


def test_evaluate_problem(cleanup):
    api.generate_inputs(CONFIGURATION_FILE_PATH, DATA_FOLDER_PATH / "inputs.xml", overwrite=True)
    api.evaluate_problem(CONFIGURATION_FILE_PATH, False)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastPathExistsError):
        api.evaluate_problem(CONFIGURATION_FILE_PATH, False)
    problem = api.evaluate_problem(CONFIGURATION_FILE_PATH, True)
    assert problem["f"] == pytest.approx(32.56910089, abs=1e-8)

    # Move output file because it will be overwritten by the optim test
    (RESULTS_FOLDER_PATH / "outputs.xml").rename(RESULTS_FOLDER_PATH / "outputs_eval.xml")


def test_optimize_problem(cleanup):
    api.generate_inputs(CONFIGURATION_FILE_PATH, DATA_FOLDER_PATH / "inputs.xml", overwrite=True)
    api.optimize_problem(CONFIGURATION_FILE_PATH, False)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastPathExistsError):
        api.optimize_problem(CONFIGURATION_FILE_PATH, False)
    problem = api.optimize_problem(CONFIGURATION_FILE_PATH, True)

    assert problem["f"] == pytest.approx(3.18339395, abs=1e-8)


def test_optimization_viewer(cleanup):
    api.generate_inputs(CONFIGURATION_FILE_PATH, DATA_FOLDER_PATH / "inputs.xml", overwrite=True)

    # Before a run
    api.optimization_viewer(CONFIGURATION_FILE_PATH)

    api.optimize_problem(CONFIGURATION_FILE_PATH, True)

    # After a run
    api.optimization_viewer(CONFIGURATION_FILE_PATH)


def test_variable_viewer(cleanup):

    file_path = DATA_FOLDER_PATH / "short_inputs.xml"

    # Using default file formatter
    api.variable_viewer(file_path)

    api.variable_viewer(file_path, editable=False)
