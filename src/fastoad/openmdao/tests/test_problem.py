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
from shutil import rmtree

import numpy as np
import pytest
from numpy.testing import assert_allclose

from fastoad.openmdao.exceptions import (
    FASTOpenMDAONanInInputFile,
)
from fastoad.openmdao.problem import FASTOADProblem
from fastoad.openmdao.variables import Variable
from .openmdao_sellar_example.sellar import Sellar
from ...io import VariableIO

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results", "problem")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_write_outputs():
    problem = FASTOADProblem()
    problem.model.add_subsystem("sellar", Sellar(), promotes=["*"])
    problem.output_file_path = pth.join(RESULTS_FOLDER_PATH, "output.xml")
    problem.setup()

    problem.write_outputs()
    variables = VariableIO(problem.output_file_path).read()
    assert variables == [
        Variable(name="f", val=1.0),
        Variable(name="g1", val=1.0),
        Variable(name="g2", val=1.0),
        Variable(name="x", val=2.0),
        Variable(name="y2", val=1.0),
        Variable(name="z", val=[np.nan, np.nan], units="m**2"),
    ]

    problem["x"] = 2.0
    problem.run_model()
    problem.write_outputs()
    variables = VariableIO(problem.output_file_path).read()
    assert variables == [
        Variable(name="f", val=32.569100892077444),
        Variable(name="g1", val=-23.409095627564167),
        Variable(name="g2", val=-11.845478137832359),
        Variable(name="x", val=2.0),
        Variable(name="y2", val=12.154521862167641),
        Variable(name="z", val=[5.0, 2.0], units="m**2"),
    ]


def test_problem_read_inputs_after_setup(cleanup):
    """Tests what happens when reading inputs using existing XML with correct var"""

    problem = FASTOADProblem()
    problem.model.add_subsystem("sellar", Sellar(), promotes=["*"])

    problem.input_file_path = pth.join(DATA_FOLDER_PATH, "ref_inputs.xml")

    problem.setup()

    assert problem.get_val(name="x") == [2.0]
    with pytest.raises(RuntimeError):
        # Several default values are defined for "z", thus OpenMDAO raises an error that
        # will be solved only after run_model() has been used.
        _ = problem.get_val(name="z", units="m**2")

    problem.read_inputs()

    problem.run_model()
    assert problem.get_val(name="x") == [2000.0]
    assert_allclose(problem.get_val(name="z", units="m**2"), [5000, 2000.0])


def test_problem_read_inputs_before_setup(cleanup):
    """Tests what happens when reading inputs using existing XML with correct var"""

    problem = FASTOADProblem()
    problem.model.add_subsystem("sellar", Sellar(), promotes=["*"])

    problem.input_file_path = pth.join(DATA_FOLDER_PATH, "ref_inputs.xml")

    problem.read_inputs()
    problem.setup()

    assert problem.get_val(name="x") == [2000.0]
    assert np.all(problem.get_val(name="z", units="m**2") == [5000.0, 2000.0])


def test_problem_read_inputs_with_nan_inputs(cleanup):
    """Tests that when reading inputs using existing XML with some nan values an exception is raised"""

    problem = FASTOADProblem()
    problem.model.add_subsystem("sellar", Sellar(), promotes=["*"])

    input_data_path = pth.join(DATA_FOLDER_PATH, "nan_inputs.xml")

    problem.input_file_path = pth.join(DATA_FOLDER_PATH, "nan_inputs.xml")

    with pytest.raises(FASTOpenMDAONanInInputFile) as exc:
        problem.read_inputs()
        assert exc.input_file_path == input_data_path
        assert exc.nan_variable_names == ["x"]

    problem.setup()

    with pytest.raises(FASTOpenMDAONanInInputFile) as exc:
        problem.read_inputs()
        assert exc.input_file_path == input_data_path
        assert exc.nan_variable_names == ["x"]
