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

import pytest
from fastoad.io import VariableIO

from tests.testing_utilities import run_system
from ..compute_aero_center import ComputeAeroCenter

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


def test_compute_aero_center(input_xml):
    """ Tests computation of aerodynamic center """

    input_list = [
        "data:geometry:wing:MAC:leading_edge:x:local",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:root:virtual_chord",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:fuselage:length",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:wing:area",
        "data:geometry:horizontal_tail:area",
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25",
        "data:aerodynamics:aircraft:cruise:CL_alpha",
        "data:aerodynamics:horizontal_tail:cruise:CL_alpha",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    problem = run_system(ComputeAeroCenter(), input_vars)

    x_ac_ratio = problem["data:aerodynamics:cruise:neutral_point:x"]
    assert x_ac_ratio == pytest.approx(0.422638, abs=1e-6)
