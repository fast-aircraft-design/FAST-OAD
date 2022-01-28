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
import openmdao.api as om
import pytest
from numpy.testing import assert_allclose

from fastoad._utils.testing import run_system
from ..mission import Mission

RESULTS_FOLDER_PATH = pth.join(
    pth.dirname(__file__), "results", pth.splitext(pth.basename(__file__))[0]
)


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_sizing_mission(cleanup, with_dummy_plugin_2):
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:main_route:cruise:altitude", 35000, units="ft")
    ivc.add_output("data:TLAR:cruise_mach", 0.78)
    ivc.add_output("data:TLAR:range", 2000, units="NM")
    ivc.add_output("data:mission:sizing:TOW", 74000, units="kg")

    ivc.add_output("data:mission:sizing:takeoff:altitude", 0.0)
    ivc.add_output("data:mission:sizing:takeoff:V2", 80.0, units="m/s")
    # FIXME : takeoff fuel should not be negative
    ivc.add_output("data:mission:sizing:takeoff:fuel", -80.0, units="kg")
    ivc.add_output("data:mission:sizing:taxi_out:thrust_rate", 0.3)
    ivc.add_output("data:mission:sizing:climb:thrust_rate", 0.9)
    ivc.add_output("data:mission:sizing:descent:thrust_rate", 0.05)
    ivc.add_output("data:mission:sizing:taxi_out:duration", 500, units="s")
    ivc.add_output("data:mission:sizing:taxi_in:thrust_rate", 0.3)
    ivc.add_output("data:mission:sizing:taxi_in:duration", 500, units="s")
    ivc.add_output("data:mission:sizing:holding:duration", 30, units="min")
    ivc.add_output("data:mission:sizing:diversion:distance", 200, units="NM")

    ivc.add_output("data:geometry:wing:area", 100.0, units="m**2")

    # Ensure L/D ratio == 16.0
    ivc.add_output("data:aerodynamics:aircraft:cruise:CL", np.linspace(0, 1.5, 150))
    ivc.add_output("data:aerodynamics:aircraft:cruise:CD", np.linspace(0, 1.5, 150) / 16.0)

    ivc.add_output("data:aerodynamics:aircraft:takeoff:CL", np.linspace(0, 1.5, 150) + 0.5)
    ivc.add_output("data:aerodynamics:aircraft:takeoff:CD", np.linspace(0, 1.5, 150) / 16.0)

    # With direct call to rubber engine
    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "sizing_mission.csv"),
            use_initializer_iteration=False,
            mission_file_path="::sizing_mission",
            adjust_fuel=False,
        ),
        ivc,
    )

    # Note: tested value are obtained by asking 1 meter of accuracy for distance routes

    assert_allclose(problem["data:mission:sizing:taxi_out:fuel"], 351.0, atol=1)
    assert_allclose(problem["data:mission:sizing:taxi_out:duration"], 500.0, atol=1)
    assert_allclose(problem["data:mission:sizing:taxi_out:distance"], 0.0, atol=1)

    assert_allclose(problem["data:mission:sizing:main_route:initial_climb:fuel"], 108.0, atol=1)
    assert_allclose(problem["data:mission:sizing:main_route:initial_climb:duration"], 30.0, atol=1)
    assert_allclose(
        problem["data:mission:sizing:main_route:initial_climb:distance"], 3163.0, atol=1
    )

    assert_allclose(problem["data:mission:sizing:main_route:climb:fuel"], 990.0, atol=1)
    assert_allclose(problem["data:mission:sizing:main_route:climb:duration"], 322.0, atol=1)
    assert_allclose(problem["data:mission:sizing:main_route:climb:distance"], 61694.0, atol=1)

    assert_allclose(problem["data:mission:sizing:main_route:cruise:fuel"], 5447.0, atol=1)
    assert_allclose(problem["data:mission:sizing:main_route:cruise:duration"], 14343.0, atol=10)
    assert_allclose(problem["data:mission:sizing:main_route:cruise:distance"], 3301263.0, atol=500)

    assert_allclose(problem["data:mission:sizing:main_route:descent:fuel"], 161.0, atol=1)
    assert_allclose(problem["data:mission:sizing:main_route:descent:duration"], 1706.0, atol=10)
    assert_allclose(problem["data:mission:sizing:main_route:descent:distance"], 337879.0, atol=500)

    assert_allclose(problem["data:mission:sizing:diversion:diversion_climb:fuel"], 470.0, atol=1)
    assert_allclose(
        problem["data:mission:sizing:diversion:diversion_climb:duration"], 153.0, atol=1
    )
    assert_allclose(
        problem["data:mission:sizing:diversion:diversion_climb:distance"], 24713.0, atol=1
    )

    assert_allclose(problem["data:mission:sizing:diversion:cruise:fuel"], 315.0, atol=1)
    assert_allclose(problem["data:mission:sizing:diversion:cruise:duration"], 880.0, atol=1)
    assert_allclose(problem["data:mission:sizing:diversion:cruise:distance"], 192513.0, atol=1)

    assert_allclose(problem["data:mission:sizing:diversion:descent:fuel"], 86.0, atol=1)
    assert_allclose(problem["data:mission:sizing:diversion:descent:duration"], 908.0, atol=1)
    assert_allclose(problem["data:mission:sizing:diversion:descent:distance"], 153173.0, atol=1)

    assert_allclose(problem["data:mission:sizing:holding:fuel"], 639.0, atol=1)
    assert_allclose(problem.get_val("data:mission:sizing:holding:duration", "s"), 1800.0, atol=1)
    assert_allclose(problem["data:mission:sizing:holding:distance"], 236663.0, atol=1)

    assert_allclose(problem["data:mission:sizing:taxi_in:fuel"], 351.0, atol=1)
    assert_allclose(problem["data:mission:sizing:taxi_in:duration"], 500.0, atol=1)
    assert_allclose(problem["data:mission:sizing:taxi_in:distance"], 0.0, atol=1)

    assert_allclose(problem["data:mission:sizing:main_route:fuel"], 6707.0, atol=1)
    assert_allclose(problem["data:mission:sizing:main_route:duration"], 16401.0, atol=10)
    assert_allclose(problem["data:mission:sizing:main_route:distance"], 3704000.0, atol=500)

    assert_allclose(problem["data:mission:sizing:diversion:fuel"], 872.0, atol=1)
    assert_allclose(problem["data:mission:sizing:diversion:duration"], 1941.0, atol=10)
    assert_allclose(
        problem.get_val("data:mission:sizing:diversion:distance", "m"), 370400.0, atol=500
    )

    assert_allclose(problem["data:mission:sizing:fuel"], 8999.0, atol=1)
    assert_allclose(problem["data:mission:sizing:duration"], 21143.0, atol=10)
    assert_allclose(problem["data:mission:sizing:distance"], 4311064.0, atol=500)

    assert_allclose(problem["data:mission:sizing:reserve:fuel"], 201.0, atol=1)

    assert_allclose(problem["data:mission:sizing:needed_block_fuel"], 9200.0, atol=1)
