"""
Test module for Overall Aircraft Design process
"""
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
from platform import system
from shutil import rmtree

import pytest
from numpy.testing import assert_allclose

from fastoad import api
from fastoad.io import VariableIO
from tests.xfoil_exe.get_xfoil import get_xfoil_path

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")

xfoil_path = None if system() == "Windows" else get_xfoil_path()


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_robustness(cleanup):
    # Testing limit cases for models and OAD process
    configuration_file_path = pth.join(DATA_FOLDER_PATH, "oad_process.toml")

    # Generation of configuration file ----------------------------------------
    # api.generate_configuration_file(configuration_file_path, True)

    # Generation of inputs ----------------------------------------------------
    # We get the same inputs as in tutorial notebook
    source_xml = pth.join(DATA_FOLDER_PATH, "CeRAS01_baseline.xml")
    api.generate_inputs(configuration_file_path, source_xml, overwrite=True)

    # Test on the limit possible range
    INPUT_FILE = pth.join(RESULTS_FOLDER_PATH, "problem_inputs.xml")
    variables_io = VariableIO(INPUT_FILE)
    var_list = variables_io.read()

    # We update the variable list (VariableList class)
    var_list["data:TLAR:range"].value = 6500.0  # [nm]
    variables_io.write(var_list)

    # Run model ---------------------------------------------------------------
    problem = api.evaluate_problem(configuration_file_path, True)

    # Verifying the number of iterations
    iter_count = (
        problem.model.wing_position_loop.cg_tail_loops.weight.iter_count
        + problem.model.wing_position_loop.cg_tail_loops.weight.iter_count_apply
    )

    assert_allclose(
        iter_count, 5464, atol=100,
    )

    # Check that weight-performances loop correctly converged
    assert_allclose(
        problem["data:weight:aircraft:OWE"],
        problem["data:weight:airframe:mass"]
        + problem["data:weight:propulsion:mass"]
        + problem["data:weight:systems:mass"]
        + problem["data:weight:furniture:mass"]
        + problem["data:weight:crew:mass"],
        atol=1,
    )
    assert_allclose(
        problem["data:weight:aircraft:MZFW"],
        problem["data:weight:aircraft:OWE"] + problem["data:weight:aircraft:max_payload"],
        atol=1,
    )
    assert_allclose(
        problem["data:weight:aircraft:MTOW"],
        problem["data:weight:aircraft:OWE"]
        + problem["data:weight:aircraft:payload"]
        + problem["data:mission:sizing:fuel"],
        atol=1,
    )

    assert_allclose(problem["data:handling_qualities:static_margin"], 0.050, atol=1e-3)
    assert_allclose(problem["data:geometry:wing:MAC:at25percent:x"], 18.289, atol=1e-2)
    assert_allclose(problem["data:weight:aircraft:MTOW"], 132917, atol=1)
    assert_allclose(problem["data:geometry:wing:area"], 269.91, atol=1e-2)
    assert_allclose(problem["data:geometry:vertical_tail:area"], 67.3, atol=1e-1)
    assert_allclose(problem["data:geometry:horizontal_tail:area"], 89.0, atol=1e-1)
    assert_allclose(problem["data:mission:sizing:fuel"], 58005, atol=1)

    api.generate_inputs(configuration_file_path, source_xml, overwrite=True)

    # Test on the limit possible range
    var_list = variables_io.read()

    # We update the variable list (VariableList class)
    var_list["data:TLAR:NPAX"].value = 300.0  # [-]
    var_list["data:TLAR:range"].value = 4000.0  # [nm]
    variables_io.write(var_list)

    # Run model ---------------------------------------------------------------
    problem = api.evaluate_problem(configuration_file_path, True)

    # Verifying the number of iterations
    iter_count = (
        problem.model.wing_position_loop.cg_tail_loops.weight.iter_count
        + problem.model.wing_position_loop.cg_tail_loops.weight.iter_count_apply
    )

    assert_allclose(
        iter_count, 4878, atol=100,
    )

    # Check that weight-performances loop correctly converged
    assert_allclose(
        problem["data:weight:aircraft:OWE"],
        problem["data:weight:airframe:mass"]
        + problem["data:weight:propulsion:mass"]
        + problem["data:weight:systems:mass"]
        + problem["data:weight:furniture:mass"]
        + problem["data:weight:crew:mass"],
        atol=1,
    )
    assert_allclose(
        problem["data:weight:aircraft:MZFW"],
        problem["data:weight:aircraft:OWE"] + problem["data:weight:aircraft:max_payload"],
        atol=1,
    )
    assert_allclose(
        problem["data:weight:aircraft:MTOW"],
        problem["data:weight:aircraft:OWE"]
        + problem["data:weight:aircraft:payload"]
        + problem["data:mission:sizing:fuel"],
        atol=1,
    )

    assert_allclose(problem["data:handling_qualities:static_margin"], 0.050, atol=1e-3)
    assert_allclose(problem["data:geometry:wing:MAC:at25percent:x"], 28.819, atol=1e-2)
    assert_allclose(problem["data:weight:aircraft:MTOW"], 186647, atol=1)
    assert_allclose(problem["data:geometry:wing:area"], 309.37, atol=1e-2)
    assert_allclose(problem["data:geometry:vertical_tail:area"], 56.1, atol=1e-1)
    assert_allclose(problem["data:geometry:horizontal_tail:area"], 105.1, atol=1e-1)
    assert_allclose(problem["data:mission:sizing:fuel"], 70820, atol=1)
