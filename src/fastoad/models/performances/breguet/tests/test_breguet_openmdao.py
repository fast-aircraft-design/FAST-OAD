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

import openmdao.api as om
from fastoad.base.flight_point import FlightPoint
from fastoad.constants import EngineSetting
from fastoad.models.propulsion.fuel_propulsion.rubber_engine import (
    OMRubberEngineComponent,
    RubberEngine,
)
from numpy.testing import assert_allclose
from scipy.constants import foot

from tests.testing_utilities import run_system
from ..openmdao import OMBreguet


def test_breguet():
    # test 1
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:main_route:cruise:altitude", 35000, units="ft")
    ivc.add_output("data:TLAR:cruise_mach", 0.78)
    ivc.add_output("data:TLAR:range", 500, units="NM")
    ivc.add_output("data:TLAR:NPAX", 150)
    ivc.add_output("data:aerodynamics:aircraft:cruise:L_D_max", 16.0)
    ivc.add_output("data:propulsion:SFC", 1e-5, units="kg/N/s")
    ivc.add_output("data:weight:aircraft:MTOW", 74000, units="kg")

    problem = run_system(OMBreguet(), ivc)

    assert_allclose(problem["data:mission:sizing:ZFW"], 65617.0, rtol=1e-3)
    assert_allclose(problem["data:mission:sizing:fuel"], 8382.0, rtol=1e-3)
    assert_allclose(problem["data:mission:sizing:fuel:unitary"], 0.0604, rtol=1e-3)
    assert_allclose(problem["data:mission:sizing:fuel:unitary"], 0.0604, rtol=1e-3)
    assert_allclose(
        problem.get_val("data:mission:sizing:main_route:climb:distance", units="km"), 250.0
    )
    assert_allclose(
        problem.get_val("data:mission:sizing:main_route:descent:distance", units="km"), 250.0
    )
    assert_allclose(
        problem.get_val("data:mission:sizing:main_route:cruise:distance", units="km"), 426.0
    )
    # test 2
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:main_route:cruise:altitude", 35000, units="ft")
    ivc.add_output("data:TLAR:cruise_mach", 0.78)
    ivc.add_output("data:TLAR:range", 1500, units="NM")
    ivc.add_output("data:TLAR:NPAX", 120)
    ivc.add_output("data:aerodynamics:aircraft:cruise:L_D_max", 16.0)
    ivc.add_output("data:propulsion:SFC", 1e-5, units="kg/N/s")
    ivc.add_output("data:weight:aircraft:MTOW", 74000, units="kg")

    problem = run_system(OMBreguet(), ivc)

    assert_allclose(problem["data:mission:sizing:ZFW"], 62473.0, rtol=1e-3)
    assert_allclose(problem["data:mission:sizing:fuel"], 11526.0, rtol=1e-3)
    assert_allclose(problem["data:mission:sizing:fuel:unitary"], 0.0346, rtol=1e-3)

    # Check consistency of other outputs
    assert_allclose(
        problem["data:mission:sizing:fuel"],
        problem["data:mission:sizing:main_route:fuel"]
        + problem["data:mission:sizing:fuel_reserve"],
        rtol=1e-3,
    )
    assert_allclose(
        problem["data:mission:sizing:main_route:fuel"],
        problem["data:mission:sizing:main_route:climb:fuel"]
        + problem["data:mission:sizing:main_route:cruise:fuel"]
        + problem["data:mission:sizing:main_route:descent:fuel"],
        rtol=1e-3,
    )


def test_breguet_with_rubber_engine():
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:main_route:cruise:altitude", 35000, units="ft")
    ivc.add_output("data:TLAR:cruise_mach", 0.78)
    ivc.add_output("data:TLAR:range", 500, units="NM")
    ivc.add_output("data:TLAR:NPAX", 150)
    ivc.add_output("data:aerodynamics:aircraft:cruise:L_D_max", 16.0)
    ivc.add_output("data:weight:aircraft:MTOW", 74000, units="kg")

    ivc.add_output("data:propulsion:rubber_engine:bypass_ratio", 5)
    ivc.add_output("data:propulsion:rubber_engine:maximum_mach", 0.95)
    ivc.add_output("data:propulsion:rubber_engine:design_altitude", 35000, units="ft")
    ivc.add_output("data:propulsion:MTO_thrust", 100000, units="N")
    ivc.add_output("data:propulsion:rubber_engine:overall_pressure_ratio", 30)
    ivc.add_output("data:propulsion:rubber_engine:turbine_inlet_temperature", 1500, units="K")

    # With rubber engine OM component
    group = om.Group()
    group.add_subsystem("breguet", OMBreguet(), promotes=["*"])
    group.add_subsystem("engine", OMRubberEngineComponent(), promotes=["*"])
    group.nonlinear_solver = om.NonlinearBlockGS()
    problem = run_system(group, ivc)

    assert_allclose(problem["data:mission:sizing:ZFW"], 65076.0, atol=1)
    assert_allclose(problem["data:mission:sizing:fuel"], 8924.0, atol=1)
    assert_allclose(problem["data:mission:sizing:fuel:unitary"], 0.0642, rtol=1e-3)

    # With direct call to rubber engine
    problem2 = run_system(OMBreguet(propulsion_id="fastoad.wrapper.propulsion.rubber_engine"), ivc)

    assert_allclose(problem2["data:mission:sizing:ZFW"], 65076.0, atol=1)
    assert_allclose(problem2["data:mission:sizing:fuel"], 8924.0, atol=1)
    assert_allclose(problem2["data:mission:sizing:fuel:unitary"], 0.0642, rtol=1e-3)

    engine = RubberEngine(5, 30, 1500, 100000, 0.95, 35000 * foot, -50)
    directly_computed_flight_point = FlightPoint(
        mach=0.78,
        altitude=35000 * foot,
        engine_setting=EngineSetting.CRUISE,
        thrust=problem["data:propulsion:required_thrust"],
    )
    engine.compute_flight_points(directly_computed_flight_point)
    assert_allclose(
        directly_computed_flight_point.sfc, problem["data:propulsion:SFC"],
    )
