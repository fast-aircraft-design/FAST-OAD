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

import openmdao.api as om
import pytest
from fastoad.io import VariableIO

from tests.testing_utilities import run_system
from ..compute_static_margin import ComputeStaticMargin

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(
    pth.dirname(__file__), "results", pth.splitext(pth.basename(__file__))[0]
)


@pytest.fixture(scope="module")
def input_xml() -> VariableIO:
    """
    :return: access to the sample xml data
    """
    # TODO: have more consistency in input data (no need for the whole geometry_inputs_full.xml)
    return VariableIO(pth.join(pth.dirname(__file__), "data", "geometry_inputs_full.xml"))


def test_compute_static_margin(input_xml):
    """ Tests computation of static margin """

    input_vars = om.IndepVarComp()
    input_vars.add_output("data:weight:aircraft:CG:aft:MAC_position", 0.438971)
    input_vars.add_output("data:aerodynamics:cruise:neutral_point:x", 0.537521)

    problem = run_system(ComputeStaticMargin(), input_vars)
    static_margin = problem["data:handling_qualities:static_margin"]
    assert static_margin == pytest.approx(0.098550, abs=1e-6)
