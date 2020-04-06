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
from ..tail_sizing.compute_ht_area import ComputeHTArea
from ..tail_sizing.compute_vt_area import ComputeVTArea

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


# pylint: disable=redefined-outer-name  # needed for pytest fixtures
@pytest.fixture(scope="module")
def input_xml() -> VariableIO:
    """
    :return: access to the sample xml data
    """
    # TODO: have more consistency in input data (no need for the whole geometry_inputs_full.xml)
    return VariableIO(pth.join(DATA_FOLDER_PATH, "hq_inputs.xml"))


def test_compute_ht_area(input_xml):
    """ Tests computation of the horizontal tail area """

    input_list = [
        "data:geometry:has_T_tail",
        "data:geometry:fuselage:length",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:area",
        "data:weight:airframe:landing_gear:main:CG:x",
        "data:weight:airframe:landing_gear:front:CG:x",
        "data:weight:aircraft:MTOW",
        "settings:weight:aircraft:CG:range",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()
    problem = run_system(ComputeHTArea(), input_vars)

    ht_lp = problem["data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"]
    assert ht_lp == pytest.approx(17.68, abs=1e-2)
    wet_area = problem["data:geometry:horizontal_tail:wetted_area"]
    assert wet_area == pytest.approx(70.31, abs=1e-2)
    ht_area = problem["data:geometry:horizontal_tail:area"]
    assert ht_area == pytest.approx(35.15, abs=1e-2)


def test_compute_vt_area(input_xml):
    """ Tests computation of the vertical tail area """

    input_list = [
        "data:TLAR:cruise_mach",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:area",
        "data:geometry:wing:span",
        "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25",
        "data:aerodynamics:vertical_tail:cruise:CL_alpha",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    input_vars.add_output("data:weight:aircraft:CG:aft:MAC_position", 0.364924)
    input_vars.add_output("data:aerodynamics:fuselage:cruise:CnBeta", -0.117901)

    component = ComputeVTArea()

    problem = run_system(component, input_vars)

    cn_beta_vt = problem["data:aerodynamics:vertical_tail:cruise:CnBeta"]
    assert cn_beta_vt == pytest.approx(0.258348, abs=1e-6)
    wet_area = problem["data:geometry:vertical_tail:wetted_area"]
    assert wet_area == pytest.approx(52.34, abs=1e-2)
    vt_area = problem["data:geometry:vertical_tail:area"]
    assert vt_area == pytest.approx(24.92, abs=1e-2)
