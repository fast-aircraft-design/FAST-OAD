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
from numpy.testing import assert_allclose
import numpy as np

from tests.testing_utilities import run_system
from ..breguet import BreguetFromMTOW, BreguetFromOWE
from ..mission import (
    _CruiseTimeSpeedDistance,
    _CruiseAltitude,
    _CruiseThrust,
    Cruise,
    CLIMB_MASS_RATIO,
)
from ...propulsion.fuel_engine.rubber_engine import OMRubberEngine


def test_cruise_time_speed_distance():
    flight_points_count = 50
    ivc = om.IndepVarComp()
    ivc.add_output(
        "data:mission:sizing:cruise:altitude", np.full(flight_points_count, 35000), units="ft"
    )
    ivc.add_output("data:TLAR:cruise_mach", np.full(flight_points_count, 0.78))
    ivc.add_output("data:mission:sizing:cruise:time:initial", 0.0)
    ivc.add_output("data:mission:sizing:cruise:distance:initial", 0.0)
    ivc.add_output("data:mission:sizing:cruise:distance:final", 500, units="NM")

    problem = run_system(_CruiseTimeSpeedDistance(flight_point_count=flight_points_count), ivc)

    assert_allclose(
        problem["data:mission:sizing:cruise:speed"],
        np.full(flight_points_count, 231.298488),
        rtol=1e-3,
    )
    assert_allclose(problem["data:mission:sizing:cruise:time:final"], 4003, rtol=1)


def test_cruise_altitude():
    flight_points_count = 5
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:cruise:altitude:initial", 35000, units="ft")
    ivc.add_output(
        "data:mission:sizing:cruise:speed", np.full(flight_points_count, 231.298488), units="m/s"
    )
    ivc.add_output(
        "data:mission:sizing:cruise:weight",
        np.linspace(
            77037 * CLIMB_MASS_RATIO, 77037 * CLIMB_MASS_RATIO * 0.5, num=flight_points_count
        ),
        units="kg",
    )
    ivc.add_output("data:aerodynamics:aircraft:cruise:optimal_CL", 0.52)
    ivc.add_output("data:geometry:aircraft:wing:area", 130.233, units="m**2")

    problem = run_system(_CruiseAltitude(flight_point_count=flight_points_count), ivc)

    assert_allclose(
        problem["data:mission:sizing:cruise:altitude"],
        np.array([10668.0, 11176.0, 12153.0, 13310.0, 14725.0]),
        atol=1,
    )


def test_cruise_thrust():
    flight_points_count = 5
    ivc = om.IndepVarComp()
    ivc.add_output("data:TLAR:cruise_mach", np.full(flight_points_count, 0.78))
    ivc.add_output(
        "data:mission:sizing:cruise:altitude", np.full(flight_points_count, 35000), units="ft"
    )
    ivc.add_output(
        "data:mission:sizing:cruise:weight",
        np.linspace(
            77037 * CLIMB_MASS_RATIO, 77037 * CLIMB_MASS_RATIO * 0.5, num=flight_points_count
        ),
        units="kg",
    )
    ivc.add_output("data:aerodynamics:aircraft:cruise:optimal_CL", 0.52)
    ivc.add_output("data:aerodynamics:aircraft:cruise:optimal_CD", 0.03414)
    ivc.add_output("data:geometry:aircraft:wing:area", 130.233, units="m**2")

    problem = run_system(_CruiseThrust(flight_point_count=flight_points_count), ivc)

    assert_allclose(
        problem["data:propulsion:required_thrust"],
        np.array([48112.0, 42098.0, 36084.0, 30070.0, 24056.0]),
        atol=1,
    )


def test_cruise_no_engine():
    flight_points_count = 5
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:cruise:consumption:initial", 0.0)
    ivc.add_output("data:TLAR:cruise_mach", np.full(flight_points_count, 0.78))
    ivc.add_output("data:mission:sizing:cruise:time:initial", 0.0)
    ivc.add_output("data:mission:sizing:cruise:distance:initial", 0.0)
    ivc.add_output("data:mission:sizing:cruise:distance:final", 500, units="NM")
    ivc.add_output("data:mission:sizing:cruise:altitude:initial", 10161.0 / 0.3048, units="ft")
    ivc.add_output("data:mission:sizing:cruise:weight:initial", 77037, units="kg")
    ivc.add_output("data:aerodynamics:aircraft:cruise:optimal_CL", 0.52)
    ivc.add_output("data:aerodynamics:aircraft:cruise:optimal_CD", 0.03414)
    ivc.add_output("data:geometry:aircraft:wing:area", 130.233, units="m**2")
    ivc.add_output("data:propulsion:SFC", np.full(flight_points_count, 1.706583172872032e-05))

    group = om.Group()
    group.add_subsystem("cruise", Cruise(flight_point_count=flight_points_count), promotes=["*"])

    problem = run_system(group, ivc)

    assert_allclose(
        problem["data:mission:sizing:cruise:altitude"],
        np.array([10161.0, 10131.0, 10202.0, 10274.0, 10345.0]),
        atol=1,
    )
    assert_allclose(
        problem["data:mission:sizing:cruise:weight"],
        np.array([77037.0, 76201.0, 75372.0, 74551.0, 73737.0]),
        atol=1,
    )


def test_cruise():
    flight_points_count = 5
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:cruise:consumption:initial", 0.0)
    ivc.add_output("data:TLAR:cruise_mach", np.full(flight_points_count, 0.78))
    ivc.add_output("data:mission:sizing:cruise:time:initial", 0.0)
    ivc.add_output("data:mission:sizing:cruise:distance:initial", 0.0)
    ivc.add_output("data:mission:sizing:cruise:distance:final", 500, units="NM")
    ivc.add_output("data:mission:sizing:cruise:altitude:initial", 10161.0 / 0.3048, units="ft")
    ivc.add_output("data:mission:sizing:cruise:weight:initial", 77037, units="kg")
    ivc.add_output("data:aerodynamics:aircraft:cruise:optimal_CL", 0.52)
    ivc.add_output("data:aerodynamics:aircraft:cruise:optimal_CD", 0.03414)
    ivc.add_output("data:geometry:aircraft:wing:area", 130.233, units="m**2")

    ivc.add_output("data:propulsion:rubber_engine:bypass_ratio", 5)
    ivc.add_output("data:propulsion:rubber_engine:maximum_mach", 0.95)
    ivc.add_output("data:propulsion:rubber_engine:design_altitude", 35000, units="ft")
    ivc.add_output("data:propulsion:MTO_thrust", 100000, units="N")
    ivc.add_output("data:propulsion:rubber_engine:overall_pressure_ratio", 30)
    ivc.add_output("data:propulsion:rubber_engine:turbine_inlet_temperature", 1500, units="K")

    group = om.Group()
    group.add_subsystem(
        "engine", OMRubberEngine(flight_point_count=flight_points_count), promotes=["*"]
    )
    group.add_subsystem("cruise", Cruise(flight_point_count=flight_points_count), promotes=["*"])
    group.nonlinear_solver = om.NonlinearBlockGS()
    group.nonlinear_solver.options["iprint"] = 0
    group.nonlinear_solver.options["maxiter"] = 100
    group.linear_solver = om.LinearBlockGS()

    problem = run_system(group, ivc)

    assert_allclose(
        problem["data:mission:sizing:cruise:altitude"],
        np.array([10161.0, 10152.0, 10242.0, 10330.0, 10415.0]),
        atol=1,
    )
    assert_allclose(
        problem["data:mission:sizing:cruise:weight"],
        np.array([77037.0, 75954.0, 74906.0, 73900.0, 72930.0]),
        atol=1,
    )
