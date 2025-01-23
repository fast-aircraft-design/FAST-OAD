#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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

from numpy.testing import assert_allclose
from scipy.constants import foot, knot

from fastoad.constants import EngineSetting, FlightPhase
from fastoad.model_base import FlightPoint

from .conftest import ClimbPhase, DescentPhase, InitialClimbPhase, TaxiPhase
from ..mission import Mission
from ..routes import RangedRoute
from ..segments.registered.cruise import CruiseSegment


def test_mission(low_speed_polar, high_speed_polar, propulsion):
    first_route_distance = 2.0e6
    second_route_distance = 5.0e5

    kwargs = dict(propulsion=propulsion, reference_area=120.0)

    taxi_out = TaxiPhase(  # This phase is here to test when mission do not start with route
        time=300.0,
        propulsion=propulsion,
    )

    first_route = RangedRoute(
        name="route_1",
        climb_phases=[
            InitialClimbPhase(
                **kwargs,
                polar=low_speed_polar,
                thrust_rate=1.0,
                name="initial_climb1",
                time_step=0.2,
            ),
            ClimbPhase(
                **kwargs,
                polar=high_speed_polar,
                thrust_rate=0.8,
                target_altitude="mach",
                maximum_mach=0.78,
                name="climb1",
                time_step=5.0,
            ),
        ],
        cruise_segment=CruiseSegment(
            **kwargs,
            target=FlightPoint(ground_distance=0.0),
            polar=high_speed_polar,
            engine_setting=EngineSetting.CRUISE,
            name=FlightPhase.CRUISE.value,
        ),
        descent_phases=[
            DescentPhase(
                **kwargs,
                polar=high_speed_polar,
                thrust_rate=0.05,
                target_altitude=1500.0 * foot,
                name=FlightPhase.DESCENT.value,
                time_step=5.0,
            )
        ],
        flight_distance=first_route_distance,
    )

    second_route = RangedRoute(
        name="route_2",
        climb_phases=[
            ClimbPhase(
                **kwargs,
                polar=high_speed_polar,
                thrust_rate=0.8,
                target_altitude=5000.0 * foot,
                maximum_mach=0.78,
                name="climb2",
                time_step=5.0,
            ),
        ],
        cruise_segment=CruiseSegment(
            **kwargs,
            target=FlightPoint(ground_distance=1.0e5),
            polar=high_speed_polar,
            engine_setting=EngineSetting.CRUISE,
            name=FlightPhase.CRUISE.value,
        ),
        descent_phases=[
            DescentPhase(
                **kwargs,
                polar=high_speed_polar,
                thrust_rate=0.05,
                target_altitude=1500.0 * foot,
                name=FlightPhase.DESCENT.value,
                time_step=5.0,
            )
        ],
        flight_distance=second_route_distance,
    )

    start = FlightPoint(
        true_airspeed=150.0 * knot,
        altitude=100.0 * foot,
        mass=70000.0,
        ground_distance=100000.0,
    )

    # Test mission with fixed route distances ----------------------------------
    mission_1 = Mission(name="mission1")
    mission_1.extend([first_route, second_route])

    flight_points = mission_1.compute_from(start)

    # plot_flight(flight_points, "test_ranged_flight.png")

    assert_allclose(
        flight_points.iloc[-1].ground_distance,
        first_route_distance + second_route_distance + start.ground_distance,
        atol=first_route.distance_accuracy,
    )
    assert_allclose(
        flight_points.mass.iloc[0] - flight_points.mass.iloc[-1],
        26953.0,
        atol=1.0,
    )
    assert_allclose(
        flight_points.iloc[0].mass - flight_points.iloc[-1].mass,
        flight_points.iloc[-1].consumed_fuel,
        atol=1e-10,
        rtol=1e-6,
    )

    # Test mission with fixed route distances and reserve ----------------------
    mission_2 = Mission(name="mission2", reserve_ratio=0.03)
    mission_2.extend([first_route, second_route])

    flight_points = mission_2.compute_from(start)

    # plot_flight(flight_points, "test_ranged_flight.png")

    assert_allclose(
        flight_points.iloc[-1].ground_distance,
        first_route_distance + second_route_distance + start.ground_distance,
        atol=first_route.distance_accuracy,
    )
    assert_allclose(
        flight_points.mass.iloc[0] - flight_points.mass.iloc[-1] + mission_2.get_reserve_fuel(),
        27593.0,
        atol=1.0,
    )

    assert_allclose(
        flight_points.iloc[0].mass - flight_points.iloc[-1].mass,
        flight_points.iloc[-1].consumed_fuel,
        atol=1e-10,
        rtol=1e-6,
    )

    # Test with objective fuel, with 2 routes ----------------------------------
    mission_3 = Mission(
        name="mission3",
        target_fuel_consumption=20000.0,
    )
    mission_3.extend([first_route, second_route])
    flight_points = mission_3.compute_from(start)
    assert_allclose(
        flight_points.mass.iloc[0] - flight_points.mass.iloc[-1],
        20000.0,
        mission_3.fuel_accuracy,
    )
    assert_allclose(
        flight_points.iloc[0].mass - flight_points.iloc[-1].mass,
        flight_points.iloc[-1].consumed_fuel,
        atol=1e-10,
        rtol=1e-6,
    )

    # Test with objective fuel, when mission does not start with a route -------
    mission_4 = Mission(name="mission4", target_fuel_consumption=20000.0)
    mission_4.extend([taxi_out, first_route, second_route])

    flight_points = mission_4.compute_from(start)
    assert_allclose(
        flight_points.mass.iloc[0] - flight_points.mass.iloc[-1],
        20000.0,
        mission_4.fuel_accuracy,
    )

    assert_allclose(
        flight_points.iloc[0].mass - flight_points.iloc[-1].mass,
        flight_points.iloc[-1].consumed_fuel,
        atol=1e-10,
        rtol=1e-6,
    )
