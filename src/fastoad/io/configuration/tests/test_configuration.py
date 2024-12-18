"""
Test module for configuration.py
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

import filecmp
import os
import shutil
import sys
import tempfile
from pathlib import Path

import openmdao.api as om
import pytest
import tomlkit
import yaml
from jsonschema import ValidationError
from ruamel.yaml import YAML

from fastoad.io import DataFile
from fastoad.io.configuration.configuration import FASTOADProblemConfigurator
from fastoad.module_management._bundle_loader import BundleLoader
from fastoad.module_management._plugins import FastoadLoader
from fastoad.module_management.exceptions import FastBundleLoaderUnknownFactoryNameError

from ..exceptions import (
    FASTConfigurationBadOpenMDAOInstructionError,
)

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results"


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    yield
    FastoadLoader.load()


def clear_openmdao_registry():
    """Useful to reset the module folder exploration between each test."""
    BundleLoader().framework.delete(force=True)


def test_problem_definition_no_input_file(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        with pytest.raises(ValidationError) as exc_info:
            conf.load(DATA_FOLDER_PATH / f"missing_input_file.{extension}")
        assert exc_info.value.message == "'input_file' is a required property"


def test_problem_definition_no_output_file(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        with pytest.raises(ValidationError) as exc_info:
            conf.load(DATA_FOLDER_PATH / f"missing_output_file.{extension}")
        assert exc_info.value.message == "'output_file' is a required property"


def test_problem_definition_no_model(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        with pytest.raises(ValidationError) as exc_info:
            conf.load(DATA_FOLDER_PATH / f"missing_model.{extension}")
        assert exc_info.value.message == "'model' is a required property"


def test_problem_definition_incorrect_attribute(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        conf.load(DATA_FOLDER_PATH / f"invalid_attribute.{extension}")
        with pytest.raises(FASTConfigurationBadOpenMDAOInstructionError) as exc_info:
            _ = conf.get_problem(read_inputs=False)
        assert exc_info.value.key == "model.cycle.other_group.nonlinear_solver"


def test_problem_definition_no_module_folder(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        conf.load(DATA_FOLDER_PATH / f"no_module_folder.{extension}")
        with pytest.raises(FastBundleLoaderUnknownFactoryNameError) as exc_info:
            conf.get_problem()
        assert exc_info.value.factory_name == "configuration_test.sellar.functions"


def test_problem_definition_module_folder_as_one_string(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        conf.load(Path(__file__).parent / "data" / f"module_folder_as_one_string.{extension}")
        conf.get_problem()


def test_problem_definition_correct_configuration(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        conf.load(DATA_FOLDER_PATH / f"valid_sellar.{extension}")
        assert Path(conf.input_file_path) == RESULTS_FOLDER_PATH / "inputs.xml"
        assert Path(conf.output_file_path) == RESULTS_FOLDER_PATH / "outputs.xml"


def test_problem_definition_with_xml_ref(cleanup, caplog):
    """Tests what happens when writing inputs using data from existing XML file"""
    for extension in ["yml", "toml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator(DATA_FOLDER_PATH / f"valid_sellar.{extension}")

        result_folder_path = RESULTS_FOLDER_PATH / "problem_definition_with_xml_ref"
        conf.input_file_path = result_folder_path / "inputs.xml"
        conf.output_file_path = result_folder_path / "outputs.xml"
        ref_input_data_path_with_nan = DATA_FOLDER_PATH / "ref_inputs_with_nan.xml"
        ref_input_data_path = DATA_FOLDER_PATH / "ref_inputs.xml"

        # Test that the presence of NaN values in inputs logs a warning
        caplog.clear()
        conf.write_needed_inputs(ref_input_data_path_with_nan)
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "WARNING"
        assert record.message == "The following variables have NaN values: ['x']"

        # Test normal process without NaN in inputs
        conf.write_needed_inputs(ref_input_data_path)
        input_data = DataFile(conf.input_file_path)
        assert len(input_data) == 2
        assert "x" in input_data.names()
        assert "z" in input_data.names()

        problem = conf.get_problem(read_inputs=True, auto_scaling=True)
        problem.setup()

        # check the global way to set options
        assert problem.model.group.functions.f.options["dummy_f_option"] == 10
        assert problem.model.group.functions.f.options["dummy_generic_option"] == "it works"
        assert problem.model.cycle.disc1.options["dummy_disc1_option"] == {"a": 1, "b": 2}
        assert problem.model.cycle.disc1.options["dummy_generic_option"] == "it works here also"

        # check that path options are made absolute
        assert (
            Path(problem.model.group.functions.options["input_path"])
            == DATA_FOLDER_PATH / "translator.txt"
        )

        assert (
            Path(problem.model_options["cycle.*"]["input_file"]) == DATA_FOLDER_PATH / "__init__.py"
        )

        # runs evaluation without optimization loop to check that inputs are taken into account
        problem.run_model()
        assert problem.model.options["assembled_jac_type"] == "csc"
        assert problem["f"] == pytest.approx(28.58830817, abs=1e-6)

        problem.write_outputs()

        # Test with alternate submodel #########################################
        alt_conf = FASTOADProblemConfigurator(
            DATA_FOLDER_PATH / f"valid_sellar_alternate.{extension}"
        )
        alt_conf.input_file_path = result_folder_path / "inputs_alt.xml"
        alt_conf.output_file_path = result_folder_path / "outputs_alt.xml"

        alt_conf.write_needed_inputs(ref_input_data_path)
        input_data = DataFile(alt_conf.input_file_path)
        assert len(input_data) == 3
        assert "x" in input_data.names()
        assert "z" in input_data.names()
        assert "bar" in input_data.names()

        alt_problem = alt_conf.get_problem(read_inputs=True, auto_scaling=True)
        # runs evaluation without optimization loop to check that inputs are taken into account
        alt_problem.setup()
        # check the global way to set options
        with pytest.raises(KeyError):
            _ = alt_problem.model.functions.f.options["dummy_f_option"]
        assert alt_problem.model.functions.f.options["dummy_generic_option"] == "it works"
        assert alt_problem.model.cycle.disc1.options["dummy_disc1_option"] == {"a": 10, "b": 20}
        assert alt_problem.model.cycle.disc1.options["dummy_generic_option"] == "it works here also"

        alt_problem.run_model()
        alt_problem.write_outputs()

        assert alt_problem.model.options["assembled_jac_type"] == "dense"
        assert alt_problem["f"] == pytest.approx(0.58830817, abs=1e-6)
        assert alt_problem["g2"] == pytest.approx(-11.94151185, abs=1e-6)
        assert alt_problem["baz"] == 42.0
        with pytest.raises(KeyError):
            alt_problem["g1"]  # submodel for g1 computation has been deactivated.


def test_problem_definition_with_xml_ref_with_indep(cleanup):
    """Tests what happens when writing inputs of a problem with indeps using data from existing XML file"""
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator(DATA_FOLDER_PATH / f"valid_sellar_with_indep.{extension}")

        result_folder_path = RESULTS_FOLDER_PATH.joinpath(
            "problem_definition_with_xml_ref_with_indep"
        )
        conf.input_file_path = result_folder_path / "inputs.xml"
        conf.output_file_path = result_folder_path / "outputs.xml"
        ref_input_data_path = DATA_FOLDER_PATH / "ref_inputs.xml"
        conf.write_needed_inputs(ref_input_data_path)
        input_data = DataFile(conf.input_file_path)
        assert len(input_data) == 2
        assert "system:x" in input_data.names()
        assert "z" in input_data.names()

        problem = conf.get_problem(read_inputs=True, auto_scaling=True)
        # runs evaluation without optimization loop to check that inputs are taken into account
        problem.setup()
        # system:x is not in ref_inputs.xml
        problem["system:x"] = 1.0
        problem.run_model()
        assert problem["f"] == pytest.approx(28.58830817, abs=1e-6)
        problem.write_outputs()


# FIXME: this test should be reworked and moved to test_problem
def test_problem_definition_with_custom_xml(cleanup):
    """Tests what happens when writing inputs using existing XML with some unwanted var"""
    conf = FASTOADProblemConfigurator(DATA_FOLDER_PATH / "valid_sellar.toml")

    result_folder_path = RESULTS_FOLDER_PATH / "problem_definition_with_custom_xml"
    conf.input_file_path = result_folder_path / "inputs.xml"
    conf.output_file_path = result_folder_path / "outputs.xml"

    input_data = DATA_FOLDER_PATH / "ref_inputs.xml"
    os.makedirs(result_folder_path, exist_ok=True)
    shutil.copy(input_data, conf.input_file_path)

    problem = conf.get_problem(read_inputs=True, auto_scaling=True)
    problem.setup()
    problem.run_model()

    assert problem["f"] == pytest.approx(28.58830817, abs=1e-6)
    problem.write_outputs()


def test_problem_definition_with_xml_ref_run_optim(cleanup):
    """
    Tests what happens when writing inputs using data from existing XML file
    and running an optimization problem
    """
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator(DATA_FOLDER_PATH / f"valid_sellar.{extension}")

        result_folder_path = RESULTS_FOLDER_PATH.joinpath(
            "problem_definition_with_xml_ref_run_optim"
        )
        conf.input_file_path = result_folder_path / "inputs.xml"
        input_data = DATA_FOLDER_PATH / "ref_inputs.xml"
        conf.write_needed_inputs(input_data)

        # Runs optimization problem with semi-analytic FD
        problem1 = conf.get_problem(read_inputs=True)
        problem1.setup()
        problem1.run_model()
        assert problem1["f"] == pytest.approx(28.58830817, abs=1e-6)
        problem1.run_driver()
        assert problem1["f"] == pytest.approx(3.18339395, abs=1e-6)
        problem1.output_file_path = result_folder_path / "outputs_1.xml"
        problem1.write_outputs()

        # Runs optimization problem with monolithic FD
        problem2 = conf.get_problem(read_inputs=True)
        problem2.model.approx_totals()
        problem2.setup()
        problem2.run_model()  # checks problem has been reset
        assert problem2["f"] == pytest.approx(28.58830817, abs=1e-6)
        problem2.run_driver()
        assert problem2["f"] == pytest.approx(3.18339395, abs=1e-6)
        problem2.output_file_path = result_folder_path / "outputs_2.xml"
        problem2.write_outputs()


def test_set_optimization_definition(cleanup):
    """
    Tests the modification of the optimization definition in the configuration file
    """
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        reference_file = DATA_FOLDER_PATH / f"valid_sellar.{extension}"
        editable_file = RESULTS_FOLDER_PATH / f"editable_valid_sellar.{extension}"

        conf = FASTOADProblemConfigurator(reference_file)

        optimization_def = {
            "design_variables": {
                "x": {"name": "x", "lower": 0, "upper": 20},
                "z": {"name": "z", "lower": 0, "upper": 10},
            },
            "constraints": {
                "gg1": {"name": "gg1", "upper": 10},
                "gg2": {"name": "gg2", "upper": 0},
            },
            "objective": {"f": {"name": "f"}},
        }

        optimization_conf = {
            "design_variables": [
                {"name": "x", "lower": 0, "upper": 20},
                {"name": "z", "lower": 0, "upper": 10},
            ],
            "constraints": [{"name": "gg1", "upper": 10}, {"name": "gg2", "upper": 0}],
            "objective": [{"name": "f"}],
        }

        read = tomlkit.loads if extension == "toml" else YAML(typ="safe").load

        with open(reference_file, "r") as file:
            d = file.read()
            conf_dict = read(d)
        conf_dict_opt = conf_dict["optimization"]
        # Should be different
        assert optimization_conf != conf_dict_opt

        conf.set_optimization_definition(optimization_def)
        conf.save(editable_file)
        with open(editable_file, "r") as file:
            d = file.read()
            conf_dict = read(d)
        conf_dict_opt = conf_dict["optimization"]
        # Should be equal
        assert optimization_conf == conf_dict_opt


def test_make_local(cleanup):
    for extension in ["toml", "yml"]:
        reference_file = DATA_FOLDER_PATH / f"valid_sellar.{extension}"
        for copy_models in [True, False]:
            clear_openmdao_registry()
            conf = FASTOADProblemConfigurator(reference_file)
            conf.input_file_path = DATA_FOLDER_PATH / "ref_inputs.xml"
            target_folder = (
                RESULTS_FOLDER_PATH / f"local_{extension}{'_with_models' if copy_models else ''}"
            )

            conf.make_local(target_folder, copy_models=copy_models)

            # Check files -----------------------------------------------------
            if copy_models:
                original_model_folder_path = DATA_FOLDER_PATH / "conf_sellar_example"
                for file_path in original_model_folder_path.rglob("*.py"):
                    copied_file_path = (
                        target_folder
                        / "models_0"
                        / "conf_sellar_example"
                        / file_path.relative_to(original_model_folder_path)
                    )
                    assert filecmp.cmp(copied_file_path, file_path)
            else:
                assert next(target_folder.glob("models_*"), None) is None

            assert filecmp.cmp(
                target_folder / "ref_inputs.xml", DATA_FOLDER_PATH / "ref_inputs.xml"
            )
            assert filecmp.cmp(
                target_folder / "group" / "functions" / "input_path" / "translator.txt",
                DATA_FOLDER_PATH / "translator.txt",
            )
            assert filecmp.cmp(
                target_folder / "model_options" / "unused_file" / "functions.py",
                DATA_FOLDER_PATH / "conf_sellar_example" / "functions.py",
            )
            assert filecmp.cmp(
                target_folder / "model_options" / "cycle." / "input_file" / "__init__.py",
                DATA_FOLDER_PATH / "__init__.py",
            )
            # Run -----------------------------------------------------
            clear_openmdao_registry()
            local_conf_1 = FASTOADProblemConfigurator(target_folder / f"valid_sellar.{extension}")
            problem = local_conf_1.get_problem(read_inputs=True)
            problem.setup()
            problem.run_model()
            problem.write_outputs()

            assert (target_folder / "outputs.xml").is_file()

            # Check that local input file is used --------------
            (target_folder / "ref_inputs.xml").unlink()

            clear_openmdao_registry()
            local_conf_2 = FASTOADProblemConfigurator(target_folder / f"valid_sellar.{extension}")
            with pytest.raises(FileNotFoundError):
                _ = local_conf_2.get_problem(read_inputs=True)

            # Check that local models are used --------------
            if copy_models:
                shutil.rmtree(target_folder / "models_0" / "conf_sellar_example")

                clear_openmdao_registry()
                local_conf_3 = FASTOADProblemConfigurator(
                    target_folder / f"valid_sellar.{extension}"
                )
                with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
                    _ = local_conf_3.get_problem(read_inputs=True)


@pytest.fixture()
def added_sys_path():
    added_paths = ["/path/to/local/code1", "/path/to/local/code2"]
    yield added_paths
    sys.path = [p for p in sys.path if p not in added_paths]


def test_sys_paths(added_sys_path):
    conf = FASTOADProblemConfigurator()
    conf.load(DATA_FOLDER_PATH / "conf_with_imports.yml")

    # Check if the paths are added to sys.path
    for path in added_sys_path:
        assert path in sys.path


def test_imports_handling(added_sys_path):
    """
    Tests the handling of imports in the configuration file
    """
    conf = FASTOADProblemConfigurator()
    conf.load(DATA_FOLDER_PATH / "conf_with_imports.yml")

    # Check that the classes are correctly imported and stored
    assert "MyDriver1" in conf._imported_classes
    assert "MyDriver2" in conf._imported_classes

    # Check that _om_eval can use the imported classes
    result1 = conf._om_eval("MyDriver1()")
    result2 = conf._om_eval("MyDriver2()")

    # Imports are done here to be sure the interpreter does not know
    # these paths when the code above is run.
    from .data.to_be_imported.my_driver_1 import MyDriver1
    from .data.to_be_imported.my_driver_2 import MyDriver2

    assert conf._imported_classes["MyDriver1"] == MyDriver1
    assert conf._imported_classes["MyDriver2"] == MyDriver2

    # Check that _om_eval can use the imported classes
    assert isinstance(result1, MyDriver1)
    assert isinstance(result2, MyDriver2)


def test_driver_configuration(added_sys_path):
    # Test advanced syntax
    config_data_new = {
        "input_file": "./inputs.xml",
        "output_file": "./outputs.xml",
        "model": {},
        "driver": {
            "instance": "om.ScipyOptimizeDriver(optimizer='COBYLA')",
            "options": {"maxiter": 100, "tol": 1e-2},
            "opt_settings": {"maxtime": 10},
        },
    }

    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".yaml") as temp_config_file:
        yaml.dump(config_data_new, temp_config_file)
        temp_config_file_path = temp_config_file.name

    configurator = FASTOADProblemConfigurator()
    configurator.load(temp_config_file_path)
    problem = configurator.get_problem()

    assert isinstance(problem.driver, om.ScipyOptimizeDriver)
    assert problem.driver.options["optimizer"] == "COBYLA"
    assert problem.driver.options["maxiter"] == 100
    assert problem.driver.options["tol"] == 1e-2
    assert problem.driver.opt_settings["maxtime"] == 10

    os.remove(temp_config_file_path)

    # Test standard syntax
    config_data_old = {
        "input_file": "./inputs.xml",
        "output_file": "./outputs.xml",
        "model": {},
        "driver": "om.ScipyOptimizeDriver(tol=1e-2, optimizer='COBYLA')",
    }

    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".yaml") as temp_config_file:
        yaml.dump(config_data_old, temp_config_file)
        temp_config_file_path = temp_config_file.name

    configurator = FASTOADProblemConfigurator()
    configurator.load(temp_config_file_path)
    problem = configurator.get_problem()

    assert isinstance(problem.driver, om.ScipyOptimizeDriver)
    assert problem.driver.options["optimizer"] == "COBYLA"
    assert problem.driver.options["tol"] == 1e-2

    os.remove(temp_config_file_path)
