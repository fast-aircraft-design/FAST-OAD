"""
test module for wing area computation
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

import openmdao.api as om
from numpy.testing import assert_allclose

from tests.testing_utilities import run_system
from ..compute_wing_area import ComputeWingArea

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


def test_compute_wing_area():
    # Driven by fuel
    ivc = om.IndepVarComp()
    ivc.add_output("data:geometry:wing:aspect_ratio", 9.48)
    ivc.add_output("data:geometry:wing:root:thickness_ratio", 0.15)
    ivc.add_output("data:geometry:wing:tip:thickness_ratio", 0.11)
    ivc.add_output("data:mission:sizing:fuel", val=20500, units="kg")
    ivc.add_output("data:TLAR:approach_speed", val=132, units="kn")
    ivc.add_output("data:weight:aircraft:MLW", val=66300, units="kg")

    ivc.add_output("data:weight:aircraft:MFW", val=21000, units="kg")
    ivc.add_output("data:aerodynamics:aircraft:landing:CL_max", val=2.80)

    problem = run_system(ComputeWingArea(), ivc)
    assert_allclose(problem["data:geometry:wing:area"], 133.97, atol=1e-2)
    assert_allclose(
        problem["data:aerodynamics:aircraft:landing:additional_CL_capacity"], 0.199, atol=1e-2
    )
    assert_allclose(problem["data:weight:aircraft:additional_fuel_capacity"], 500.0, atol=1.0)

    # Driven by CL max
    ivc = om.IndepVarComp()
    ivc.add_output("data:geometry:wing:aspect_ratio", 9.48)
    ivc.add_output("data:geometry:wing:root:thickness_ratio", 0.15)
    ivc.add_output("data:geometry:wing:tip:thickness_ratio", 0.11)
    ivc.add_output("data:mission:sizing:fuel", val=15000, units="kg")
    ivc.add_output("data:TLAR:approach_speed", val=132, units="kn")
    ivc.add_output("data:weight:aircraft:MLW", val=66300, units="kg")

    ivc.add_output("data:weight:aircraft:MFW", val=21000, units="kg")
    ivc.add_output("data:aerodynamics:aircraft:landing:CL_max", val=2.80)

    problem = run_system(ComputeWingArea(), ivc)
    assert_allclose(problem["data:geometry:wing:area"], 124.38, atol=1e-2)
    assert_allclose(
        problem["data:aerodynamics:aircraft:landing:additional_CL_capacity"], 0.0, atol=1e-2
    )
    assert_allclose(problem["data:weight:aircraft:additional_fuel_capacity"], 6000.0, atol=1.0)
