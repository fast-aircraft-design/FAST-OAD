"""
Test module for configuration.py
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
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
from shutil import rmtree, copy

import numpy as np
import openmdao.api as om
import pytest
import tomlkit as toml

from .. import (
    FASTOADProblem,
    FASTConfigurationNoProblemDefined,
    FASTConfigurationBadOpenMDAOInstructionError,
)

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_problem_definition(cleanup):
    """ Test problem definition from configuration files """
    # Missing problem
    problem = FASTOADProblem()
    with pytest.raises(FASTConfigurationNoProblemDefined) as exc_info:
        problem.configure(pth.join(pth.dirname(__file__), "data", "missing_problem.toml"))
    assert exc_info is not None

    # Incorrect attribute
    problem = FASTOADProblem()
    with pytest.raises(FASTConfigurationBadOpenMDAOInstructionError) as exc_info:
        problem.configure(pth.join(pth.dirname(__file__), "data", "invalid_attribute.toml"))
    problem.read_inputs()
    assert exc_info is not None
    assert exc_info.value.key == "model.cycle.other_group.nonlinear_solver"

    # Reading of a minimal problem (model = explicitcomponent)
    problem = FASTOADProblem()
    problem.configure(pth.join(pth.dirname(__file__), "data", "disc1.toml"))
    assert isinstance(problem.model.system, om.ExplicitComponent)

    # Reading of correct problem definition
    problem = FASTOADProblem()
    problem.configure(pth.join(pth.dirname(__file__), "data", "valid_sellar.toml"))

    # Just running these methods to check there is no crash. As simple assemblies of
    # other methods, their results should already be unit-tested.
    problem.write_needed_inputs()
    problem.read_inputs()

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
    problem = FASTOADProblem()
    problem.configure(pth.join(DATA_FOLDER_PATH, "valid_sellar.toml"))

    input_data = pth.join(DATA_FOLDER_PATH, "ref_inputs.xml")
    problem.write_needed_inputs(input_data)
    problem.read_inputs()

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
    problem = FASTOADProblem()
    problem.configure(pth.join(DATA_FOLDER_PATH, "valid_sellar.toml"))

    input_data = pth.join(DATA_FOLDER_PATH, "ref_inputs.xml")
    problem.write_needed_inputs(input_data)

    # Runs optimization problem with semi-analytic FD
    problem.read_inputs()
    problem.setup()
    problem.run_model()
    assert problem["f"] == pytest.approx(28.58830817, abs=1e-6)
    problem.run_driver()
    assert problem["f"] == pytest.approx(3.18339395, abs=1e-6)

    # Runs optimization problem with monolithic FD
    problem.build_model()
    problem.read_inputs()  # resets the problem
    problem.model.approx_totals()
    problem.setup()
    problem.run_model()  # checks problem has been reset
    assert problem["f"] == pytest.approx(28.58830817, abs=1e-6)
    problem.run_driver()
    assert problem["f"] == pytest.approx(3.18339395, abs=1e-6)


def test_write_optimization_definition(cleanup):
    """
    Tests the modification of the optimization definition in the .toml
    configuration file
    """
    reference_file = pth.join(DATA_FOLDER_PATH, "valid_sellar.toml")
    editable_file = pth.join(RESULTS_FOLDER_PATH, "editable_valid_sellar.toml")

    copy(reference_file, editable_file)

    problem = FASTOADProblem()
    problem.configure(editable_file)

    optimization_def = {
        "design_var": {
            "x": {"name": "x", "lower": 0, "upper": 20},
            "z": {"name": "z", "lower": 0, "upper": 10},
        },
        "constraint": {"g1": {"name": "g1", "upper": 10}, "g2": {"name": "g2", "upper": 0},},
        "objective": {"f": {"name": "f"}},
    }

    optimization_conf = {
        "design_var": [
            {"name": "x", "lower": 0, "upper": 20},
            {"name": "z", "lower": 0, "upper": 10},
        ],
        "constraint": [{"name": "g1", "upper": 10}, {"name": "g2", "upper": 0}],
        "objective": [{"name": "f"}],
    }

    with open(editable_file, "r") as file:
        d = file.read()
        conf_dict = toml.loads(d)
    conf_dict_opt = conf_dict["optimization"]
    # Should be different
    assert optimization_conf != conf_dict_opt

    problem._write_optimization_definition(optimization_def)
    with open(editable_file, "r") as file:
        d = file.read()
        conf_dict = toml.loads(d)
    conf_dict_opt = conf_dict["optimization"]
    # Should be equal
    assert optimization_conf == conf_dict_opt
