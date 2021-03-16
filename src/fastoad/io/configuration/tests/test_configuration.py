"""
Test module for configuration.py
"""
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
from shutil import rmtree

import numpy as np
import openmdao.api as om
import pytest
import tomlkit
from jsonschema import ValidationError
from ruamel import yaml

from fastoad.io.configuration.configuration import FASTOADProblemConfigurator
from fastoad.module_management import BundleLoader
from fastoad.module_management.exceptions import FastBundleLoaderUnknownFactoryNameError
from fastoad.module_management.plugins import load_plugins
from ..exceptions import FASTConfigurationBadOpenMDAOInstructionError

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    yield
    load_plugins()


def clear_openmdao_registry():
    """Useful to reset the module folder exploration between each test."""
    BundleLoader().framework.delete(force=True)


def test_problem_definition_no_input_file(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        with pytest.raises(ValidationError) as exc_info:
            conf.load(pth.join(pth.dirname(__file__), "data", "missing_input_file.%s" % extension))
        assert exc_info.value.message == "'input_file' is a required property"


def test_problem_definition_no_output_file(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        with pytest.raises(ValidationError) as exc_info:
            conf.load(pth.join(pth.dirname(__file__), "data", "missing_output_file.%s" % extension))
        assert exc_info.value.message == "'output_file' is a required property"


def test_problem_definition_no_model(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        with pytest.raises(ValidationError) as exc_info:
            conf.load(pth.join(pth.dirname(__file__), "data", "missing_model.%s" % extension))
        assert exc_info.value.message == "'model' is a required property"


def test_problem_definition_incorrect_attribute(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        conf.load(pth.join(pth.dirname(__file__), "data", "invalid_attribute.%s" % extension))
        with pytest.raises(FASTConfigurationBadOpenMDAOInstructionError) as exc_info:
            problem = conf.get_problem(read_inputs=False)
        assert exc_info.value.key == "model.cycle.other_group.nonlinear_solver"


def test_problem_definition_no_module_folder(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        conf.load(pth.join(pth.dirname(__file__), "data", "no_module_folder.%s" % extension))
        with pytest.raises(FastBundleLoaderUnknownFactoryNameError) as exc_info:
            conf.get_problem()
        assert exc_info.value.factory_name == "configuration_test.sellar.functions"


def test_problem_definition_module_folder_as_one_string(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        conf.load(
            pth.join(pth.dirname(__file__), "data", "module_folder_as_one_string.%s" % extension)
        )
        conf.get_problem()


def test_problem_definition_correct_configuration(cleanup):
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator()
        conf.load(pth.join(pth.dirname(__file__), "data", "valid_sellar.%s" % extension))
        assert conf.input_file_path == pth.join(RESULTS_FOLDER_PATH, "inputs.xml")
        assert conf.output_file_path == pth.join(RESULTS_FOLDER_PATH, "outputs.xml")

        # Just running these methods to check there is no crash. As simple assemblies of
        # other methods, their results should already be unit-tested.
        conf.write_needed_inputs()
        problem = conf.get_problem(read_inputs=True)

        problem.setup()
        assert isinstance(problem.model.cycle, om.Group)
        assert isinstance(problem.model.cycle.disc1, om.ExplicitComponent)
        assert isinstance(problem.model.cycle.disc2, om.ExplicitComponent)
        assert isinstance(problem.model.functions, om.ExplicitComponent)

        assert isinstance(problem.driver, om.ScipyOptimizeDriver)
        assert problem.driver.options["optimizer"] == "SLSQP"
        assert isinstance(problem.model.cycle.nonlinear_solver, om.NonlinearBlockGS)

        problem.run_driver()

        problem.run_model()
        assert np.isnan(problem["f"])


def test_problem_definition_with_xml_ref(cleanup):
    """ Tests what happens when writing inputs using data from existing XML file"""
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        conf = FASTOADProblemConfigurator(pth.join(DATA_FOLDER_PATH, "valid_sellar.%s" % extension))

        input_data = pth.join(DATA_FOLDER_PATH, "ref_inputs.xml")
        conf.write_needed_inputs(input_data)

        problem = conf.get_problem(read_inputs=True, auto_scaling=True)
        # runs evaluation without optimization loop to check that inputs are taken into account
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
        conf = FASTOADProblemConfigurator(pth.join(DATA_FOLDER_PATH, "valid_sellar.%s" % extension))

        input_data = pth.join(DATA_FOLDER_PATH, "ref_inputs.xml")
        conf.write_needed_inputs(input_data)

        # Runs optimization problem with semi-analytic FD
        problem1 = conf.get_problem(read_inputs=True)
        problem1.setup()
        problem1.run_model()
        assert problem1["f"] == pytest.approx(28.58830817, abs=1e-6)
        problem1.run_driver()
        assert problem1["f"] == pytest.approx(3.18339395, abs=1e-6)

        # Runs optimization problem with monolithic FD
        problem2 = conf.get_problem(read_inputs=True)
        problem2.model.approx_totals()
        problem2.setup()
        problem2.run_model()  # checks problem has been reset
        assert problem2["f"] == pytest.approx(28.58830817, abs=1e-6)
        problem2.run_driver()
        assert problem2["f"] == pytest.approx(3.18339395, abs=1e-6)


def test_set_optimization_definition(cleanup):
    """
    Tests the modification of the optimization definition in the configuration file
    """
    for extension in ["toml", "yml"]:
        clear_openmdao_registry()
        reference_file = pth.join(DATA_FOLDER_PATH, "valid_sellar.%s" % extension)
        editable_file = pth.join(RESULTS_FOLDER_PATH, "editable_valid_sellar.%s" % extension)

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

        read = tomlkit.loads if extension == "toml" else yaml.safe_load

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
