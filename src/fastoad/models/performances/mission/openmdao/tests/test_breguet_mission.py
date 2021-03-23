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

import numpy as np
import openmdao.api as om
from numpy.testing import assert_allclose

from tests.testing_utilities import run_system
from ..mission import Mission


def test_breguet_with_rubber_engine():
    # Ensures Breguet mission gives same results as previous Breguet-only component
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:main_route:cruise:altitude", 35000, units="ft")
    ivc.add_output("data:TLAR:cruise_mach", 0.78)
    ivc.add_output("data:TLAR:range", 500, units="NM")
    ivc.add_output("data:TLAR:NPAX", 150)
    ivc.add_output("data:mission:sizing:TOW", 74000, units="kg")

    ivc.add_output("data:propulsion:rubber_engine:bypass_ratio", 5)
    ivc.add_output("data:propulsion:rubber_engine:maximum_mach", 0.95)
    ivc.add_output("data:propulsion:rubber_engine:design_altitude", 35000, units="ft")
    ivc.add_output("data:propulsion:MTO_thrust", 100000, units="N")
    ivc.add_output("data:propulsion:rubber_engine:overall_pressure_ratio", 30)
    ivc.add_output("data:propulsion:rubber_engine:turbine_inlet_temperature", 1500, units="K")

    ivc.add_output("settings:mission:sizing:breguet:climb:mass_ratio", 0.97)
    ivc.add_output("settings:mission:sizing:breguet:descent:mass_ratio", 0.98)
    ivc.add_output("settings:mission:sizing:breguet:reserve:mass_ratio", 0.06)
    ivc.add_output("data:mission:sizing:takeoff:V2", 0.0, units="m/s")
    ivc.add_output("data:mission:sizing:takeoff:fuel", 0.0, units="kg")
    ivc.add_output("data:mission:sizing:taxi_out:thrust_rate", 0)
    ivc.add_output("data:mission:sizing:taxi_out:duration", 0, units="s")
    ivc.add_output("data:geometry:wing:area", 0.0, units="m**2")
    ivc.add_output("data:mission:sizing:takeoff:altitude", 0.0)

    # Ensure L/D ratio == 16.0
    ivc.add_output("data:aerodynamics:aircraft:cruise:CL", np.linspace(0, 1.5, 150))
    ivc.add_output("data:aerodynamics:aircraft:cruise:CD", np.linspace(0, 1.5, 150) / 16.0)

    # With direct call to rubber engine
    problem = run_system(
        Mission(
            propulsion_id="fastoad.wrapper.propulsion.rubber_engine",
            use_initializer_iteration=False,
            mission_file_path="::sizing_breguet",
            adjust_fuel=False,
        ),
        ivc,
    )

    assert_allclose(problem["data:mission:sizing:main_route:climb:fuel"], 2220.0, atol=1)
    assert_allclose(problem["data:mission:sizing:main_route:cruise:fuel"], 1391.0, atol=1)
    assert_allclose(problem["data:mission:sizing:main_route:descent:fuel"], 1408.0, atol=1)
    assert_allclose(problem["data:mission:sizing:main_route:cruise:distance"], 426000.0, atol=1)
    assert_allclose(problem["data:mission:sizing:needed_block_fuel"], 8924.0, atol=1)
