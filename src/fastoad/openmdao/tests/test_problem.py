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
from os import makedirs
from shutil import rmtree

import numpy as np
import openmdao.api as om
import pytest
from numpy.testing import assert_allclose

from fastoad.openmdao.exceptions import (
    FASTOpenMDAONanInInputFile,
)
from fastoad.openmdao.problem import FASTOADProblem
from fastoad.openmdao.variables import Variable, VariableList
from .openmdao_sellar_example.sellar import Sellar
from ...io import VariableIO

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results", "problem")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    makedirs(RESULTS_FOLDER_PATH)


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
    problem["z"] = [
        5.0,
        2.0,
    ]  # Since version 3.17 of OpenMDAO, the np.nan input definition of z is chosen.

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
    assert_allclose(problem.get_val(name="x"), 1.0)
    assert_allclose(problem.get_val(name="z", units="m**2"), [4.0, 3.0])
    assert_allclose(problem["f"], 21.7572, atol=1.0e-4)


def test_problem_read_inputs_before_setup(cleanup):
    """Tests what happens when reading inputs using existing XML with correct var"""

    problem = FASTOADProblem()
    problem.model.add_subsystem("sellar", Sellar(), promotes=["*"])

    problem.input_file_path = pth.join(DATA_FOLDER_PATH, "ref_inputs.xml")

    problem.read_inputs()
    problem.setup()
    problem.run_model()

    assert_allclose(problem.get_val(name="x"), 1.0)
    assert_allclose(problem.get_val(name="z", units="m**2"), [4.0, 3.0])
    assert_allclose(problem["f"], 21.7572, atol=1.0e-4)


def test_problem_with_case_recorder(cleanup):
    """Tests what happens when using a case recorder"""
    # Adding a case recorder may cause a crash in case of deepcopy.

    problem = FASTOADProblem()
    sellar = Sellar()
    sellar.nonlinear_solver = om.NonlinearBlockGS()  # Solver that is compatible with deepcopy
    sellar.add_recorder(om.SqliteRecorder(pth.join(RESULTS_FOLDER_PATH, "cases.sql")))

    problem.model.add_subsystem("sellar", sellar, promotes=["*"])

    problem.input_file_path = pth.join(DATA_FOLDER_PATH, "ref_inputs.xml")

    problem.setup()
    problem.read_inputs()
    problem.run_model()

    assert_allclose(problem.get_val(name="x"), 1.0)
    assert_allclose(problem.get_val(name="z", units="m**2"), [4.0, 3.0])
    assert_allclose(problem["f"], 21.7572, atol=1.0e-4)


def test_problem_read_inputs_with_nan_inputs(cleanup):
    """Tests that when reading inputs using existing XML with some nan values an exception is raised"""

    problem = FASTOADProblem()
    problem.model.add_subsystem("sellar", Sellar(), promotes=["*"])

    input_data_path = pth.join(DATA_FOLDER_PATH, "nan_inputs.xml")

    problem.input_file_path = pth.join(DATA_FOLDER_PATH, "nan_inputs.xml")

    with pytest.raises(FASTOpenMDAONanInInputFile) as exc_info:
        problem.read_inputs()
        assert exc_info.value.input_file_path == input_data_path
        assert exc_info.value.nan_variable_names == ["x"]

    problem.setup()

    with pytest.raises(FASTOpenMDAONanInInputFile) as exc_info:
        problem.read_inputs()
        assert exc_info.value.input_file_path == input_data_path
        assert exc_info.value.nan_variable_names == ["x"]


def test_problem_with_dynamically_shaped_inputs(cleanup):
    class MyComp1(om.ExplicitComponent):
        def setup(self):
            self.add_input("x", shape_by_conn=True, copy_shape="y")
            self.add_output("y", shape_by_conn=True, copy_shape="x")

        def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
            outputs["y"] = 10 * inputs["x"]

    class MyComp2(om.ExplicitComponent):
        def setup(self):
            self.add_input("y", shape_by_conn=True, copy_shape="z")
            self.add_output("z", shape_by_conn=True, copy_shape="y")

        def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
            outputs["z"] = 0.1 * inputs["y"]

    # --------------------------------------------------------------------------
    # With these 2 components, an OpenMDAO problem won't pass the setup due to
    # the non-determined shapes
    vanilla_problem = om.Problem()
    vanilla_problem.model.add_subsystem("comp1", MyComp1(), promotes=["*"])
    vanilla_problem.model.add_subsystem("comp2", MyComp2(), promotes=["*"])
    with pytest.raises(RuntimeError):
        vanilla_problem.setup()

    # --------------------------------------------------------------------------
    # ... But fastoad problem will do the setup and provide dummy shapes
    # when needed
    fastoad_problem = FASTOADProblem()
    fastoad_problem.model.add_subsystem("comp1", MyComp1(), promotes=["*"])
    fastoad_problem.model.add_subsystem("comp2", MyComp2(), promotes=["*"])
    fastoad_problem.setup()
    assert (
        fastoad_problem["x"].shape
        == fastoad_problem["y"].shape
        == fastoad_problem["z"].shape
        == (2,)
    )

    # In such case, reading inputs after the setup will make run_model fail, because dummy shapes
    # have already been provided, and will probably not match the ones in input file.
    fastoad_problem.input_file_path = pth.join(DATA_FOLDER_PATH, "dynamic_shape_inputs_1.xml")
    fastoad_problem.read_inputs()
    with pytest.raises(ValueError):
        fastoad_problem.run_model()

    # --------------------------------------------------------------------------
    # If input reading is done before setup, all is fine.
    fastoad_problem = FASTOADProblem()
    fastoad_problem.model.add_subsystem("comp1", MyComp1(), promotes=["*"])
    fastoad_problem.model.add_subsystem("comp2", MyComp2(), promotes=["*"])
    fastoad_problem.input_file_path = pth.join(DATA_FOLDER_PATH, "dynamic_shape_inputs_1.xml")
    fastoad_problem.read_inputs()
    fastoad_problem.setup()

    inputs = VariableList.from_problem(fastoad_problem, io_status="inputs")
    assert inputs.names() == ["x"]
    outputs = VariableList.from_problem(fastoad_problem, io_status="outputs")
    assert outputs.names() == ["y", "z"]
    variables = VariableList.from_problem(fastoad_problem)
    assert variables.names() == ["x", "y", "z"]

    fastoad_problem.run_model()

    assert_allclose(fastoad_problem["x"], [1.0, 2.0, 5.0])
    assert_allclose(fastoad_problem["y"], [10.0, 20.0, 50.0])
    assert_allclose(fastoad_problem["z"], [1.0, 2.0, 5.0])

    # --------------------------------------------------------------------------
    # In the case variables are shaped from "downstream", OpenMDAO works OK.
    class MyComp3(om.ExplicitComponent):
        def setup(self):
            self.add_input("z", shape=(3,))
            self.add_output("a")

        def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
            outputs["a"] = np.sum(inputs["z"])

    fastoad_problem = FASTOADProblem()
    fastoad_problem.model.add_subsystem("comp1", MyComp1(), promotes=["*"])
    fastoad_problem.model.add_subsystem("comp2", MyComp2(), promotes=["*"])
    fastoad_problem.model.add_subsystem("comp3", MyComp3(), promotes=["*"])

    inputs = VariableList.from_problem(fastoad_problem, io_status="inputs")
    assert inputs.names() == ["x"]
    outputs = VariableList.from_problem(fastoad_problem, io_status="outputs")
    assert outputs.names() == ["y", "z", "a"]
    variables = VariableList.from_problem(fastoad_problem)
    assert variables.names() == ["x", "y", "z", "a"]

    fastoad_problem.setup()
    fastoad_problem.run_model()
