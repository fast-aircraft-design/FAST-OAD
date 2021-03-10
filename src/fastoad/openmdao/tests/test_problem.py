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

import pytest

from fastoad.openmdao.problem import FASTOADProblem
from fastoad.openmdao.variables import Variable
from .openmdao_sellar_example.sellar import Sellar
from ...io import VariableIO

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
        Variable(name="f", value=1.0),
        Variable(name="g1", value=1.0),
        Variable(name="g2", value=1.0),
        Variable(name="x", value=2),
        Variable(name="y2", value=1.0),
        Variable(name="z", value=[5.0, 2.0], units="m**2"),
    ]

    problem.run_model()
    problem.write_outputs()
    variables = VariableIO(problem.output_file_path).read()
    assert variables == [
        Variable(name="f", value=32.569100892077444),
        Variable(name="g1", value=-23.409095627564167),
        Variable(name="g2", value=-11.845478137832359),
        Variable(name="x", value=2),
        Variable(name="y2", value=12.154521862167641),
        Variable(name="z", value=[5.0, 2.0], units="m**2"),
    ]
