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


from numpy.testing import assert_allclose
from scipy.constants import foot

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet
from .conftest import DummyEngine
from ..altitude_change import AltitudeChangeSegment


def test_climb_fixed_altitude_at_constant_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=10000.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
    )  # not constant TAS order, as it is the default
    segment.thrust_rate = 1.0
    segment.time_step = 2.0
    flight_points = segment.compute_from(
        FlightPoint(altitude=5000.0, mass=70000.0, true_airspeed=150.0)
    )  # Test with dict

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.altitude, 10000.0)
    assert_allclose(last_point.true_airspeed, 150.0)
    assert_allclose(last_point.time, 143.5, rtol=1e-2)
    assert_allclose(last_point.mass, 69713.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 20943.0, rtol=1e-3)
    assert last_point.engine_setting == EngineSetting.CLIMB


def test_climb_fixed_altitude_at_constant_EAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    flight_points = AltitudeChangeSegment(
        target=FlightPoint(altitude=10000.0, equivalent_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
        engine_setting=EngineSetting.CRUISE,  # The engine model does not use this setting
    ).compute_from(FlightPoint(altitude=5000.0, mass=70000.0, equivalent_airspeed=100.0))

    first_point = flight_points.iloc[0]
    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.altitude, 10000.0)
    assert_allclose(last_point.equivalent_airspeed, 100.0)
    assert_allclose(last_point.time, 145.2, rtol=1e-2)
    assert_allclose(first_point.true_airspeed, 129.0, atol=0.1)
    assert_allclose(last_point.true_airspeed, 172.3, atol=0.1)
    assert_allclose(last_point.mass, 69710.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 20915.0, rtol=1e-3)
    assert last_point.engine_setting == EngineSetting.CRUISE


def test_climb_optimal_altitude_at_fixed_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    flight_points = AltitudeChangeSegment(
        target=FlightPoint(
            altitude=AltitudeChangeSegment.OPTIMAL_ALTITUDE, true_airspeed="constant"
        ),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
    ).compute_from(FlightPoint(altitude=5000.0, true_airspeed=250.0, mass=70000.0))

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.altitude, 10085.0, atol=0.1)
    assert_allclose(last_point.true_airspeed, 250.0)
    assert_allclose(last_point.time, 84.1, rtol=1e-2)
    assert_allclose(last_point.mach, 0.8359, rtol=1e-4)
    assert_allclose(last_point.mass, 69832.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 20401.0, rtol=1e-3)


def test_climb_optimal_flight_level_at_fixed_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    flight_points = AltitudeChangeSegment(
        target=FlightPoint(
            altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL, true_airspeed="constant"
        ),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
    ).compute_from(FlightPoint(altitude=5000.0, true_airspeed=250.0, mass=70000.0))

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(flight_points.true_airspeed, 250.0)
    assert_allclose(last_point.altitude / foot, 32000.0, atol=0.1)
    assert_allclose(last_point.time, 78.7, rtol=1e-2)
    assert_allclose(last_point.mach, 0.8318, rtol=1e-4)
    assert_allclose(last_point.mass, 69843.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 19091.0, rtol=1e-3)


def test_climb_optimal_flight_level_at_fixed_mach(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    flight_points = AltitudeChangeSegment(
        target=FlightPoint(altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL, mach="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
    ).compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0))

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(flight_points.mach, 0.82)
    assert_allclose(last_point.altitude / foot, 32000.0, atol=0.1)
    assert_allclose(last_point.time, 77.5, rtol=1e-2)
    assert_allclose(last_point.true_airspeed, 246.44, rtol=1e-4)
    assert_allclose(last_point.mass, 69843.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 19179.0, rtol=1e-3)


def test_climb_optimal_flight_level_at_fixed_mach_with_capped_flight_level(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    flight_points = AltitudeChangeSegment(
        target=FlightPoint(altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL, mach="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        maximum_flight_level=300.0,
        time_step=0.01,
    ).compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0))

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(flight_points.mach, 0.82)
    assert_allclose(last_point.altitude / foot, 30000.0, atol=0.1)
    assert_allclose(last_point.time, 67.5, rtol=1e-2)
    assert_allclose(last_point.true_airspeed, 248.6, rtol=1e-4)
    assert_allclose(last_point.mass, 69865.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 16762.0, rtol=1e-3)


def test_climb_not_enough_thrust(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=10000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=0.1,
    )
    assert (
        len(segment.compute_from(FlightPoint(altitude=5000.0, true_airspeed=150.0, mass=70000.0)))
        == 1
    )


def test_descent_to_fixed_altitude_at_constant_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    flight_points = AltitudeChangeSegment(
        target=FlightPoint(altitude=5000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=100.0,
        polar=polar,
        thrust_rate=0.1,
        time_step=2.0,
    ).compute_from(
        FlightPoint(altitude=10000.0, true_airspeed=200.0, mass=70000.0, time=2000.0)
    )  # And we define a non-null start time

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.altitude, 5000.0)
    assert_allclose(last_point.true_airspeed, 200.0)
    assert_allclose(last_point.time, 3370.4, rtol=1e-2)
    assert_allclose(last_point.mass, 69849.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 274043.0, rtol=1e-3)


def test_descent_to_fixed_altitude_at_constant_EAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    flight_points = AltitudeChangeSegment(
        target=FlightPoint(altitude=5000.0, equivalent_airspeed="constant"),
        propulsion=propulsion,
        reference_area=100.0,
        polar=polar,
        thrust_rate=0.1,
        time_step=2.0,
    ).compute_from(FlightPoint(altitude=10000.0, equivalent_airspeed=200.0, mass=70000.0))

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.altitude, 5000.0)
    assert_allclose(last_point.equivalent_airspeed, 200.0)
    assert_allclose(last_point.time, 821.4, rtol=1e-2)
    assert_allclose(last_point.mass, 69910.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 243155.0, rtol=1e-3)


def test_descent_to_fixed_EAS_at_constant_mach(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    flight_points = AltitudeChangeSegment(
        target=FlightPoint(equivalent_airspeed=150.0, mach="constant"),
        propulsion=propulsion,
        reference_area=100.0,
        polar=polar,
        thrust_rate=0.1,
        # time_step=5.0, # we use default time step
    ).compute_from(FlightPoint(altitude=10000.0, mass=70000.0, mach=0.78))

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.equivalent_airspeed, 150.0)
    assert_allclose(last_point.mach, 0.78)
    assert_allclose(last_point.time, 343.6, rtol=1e-2)
    assert_allclose(last_point.altitude, 8654.0, atol=1.0)
    assert_allclose(last_point.true_airspeed, 238.1, atol=0.1)
    assert_allclose(last_point.mass, 69962.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 81042.0, rtol=1e-3)
