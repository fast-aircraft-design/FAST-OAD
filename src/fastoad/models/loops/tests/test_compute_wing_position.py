"""
test module for wing position computation
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

import openmdao.api as om
from numpy.testing import assert_allclose

from tests.testing_utilities import run_system
from ..compute_wing_position import ComputeWingPosition

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


def test_compute_wing_position():
    # The component is unit tested without being converged as it would require the geometry module
    ivc = om.IndepVarComp()

    ivc.add_output("data:handling_qualities:static_margin", val=0.1)
    ivc.add_output("data:handling_qualities:static_margin:target", val=0.05)
    ivc.add_output("data:geometry:wing:MAC:length", val=4.262)
    ivc.add_output("data:weight:aircraft:CG:aft:MAC_position", val=0.361)
    ivc.add_output("data:weight:aircraft:CG:aft:x", val=17.545)

    problem = run_system(ComputeWingPosition(), ivc)
    assert_allclose(problem["data:geometry:wing:MAC:at25percent:x"], 16.86, atol=1e-1)
