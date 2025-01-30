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

import pytest
from numpy.testing import assert_allclose

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet

from .conftest import DummyEngine, DummyUnpickableEngine
from ..altitude_change import AltitudeChangeSegment
from ..cruise import (
    BreguetCruiseSegment,
    ClimbAndCruiseSegment,
    CruiseSegment,
    OptimalCruiseSegment,
)


def test_cruise_at_constant_altitude(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = CruiseSegment(
        target=FlightPoint(ground_distance=5.0e5),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CRUISE,  # The engine model does not use this setting
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(mass=70000.0, altitude=10000.0, mach=0.78, ground_distance=1000.0)
        )

        first_point = flight_points.iloc[0]
        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.05s as time step
        assert_allclose(first_point.altitude, 10000.0)
        assert_allclose(first_point.true_airspeed, 233.6, atol=0.1)
        assert first_point.engine_setting == EngineSetting.CRUISE

        assert_allclose(last_point.ground_distance, 501000.0)
        assert_allclose(last_point.altitude, 10000.0)
        assert_allclose(last_point.time, 2141.0, rtol=1e-2)
        assert_allclose(last_point.true_airspeed, 233.6, atol=0.1)
        assert_allclose(last_point.mass, 69568.0, rtol=1e-4)
        assert last_point.engine_setting == EngineSetting.CRUISE

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_breguet_cruise(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = BreguetCruiseSegment(
        target=FlightPoint(ground_distance=5.0e5),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CRUISE,  # The engine model does not use this setting
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(time=10000.0, mass=70000.0, altitude=10000.0, mach=0.78)
        )

        first_point = flight_points.iloc[0]
        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with CruiseSegment and 0.05s as
        # time step
        assert_allclose(first_point.altitude, 10000.0)
        assert_allclose(first_point.true_airspeed, 233.6, atol=0.1)
        assert first_point.engine_setting == EngineSetting.CRUISE

        assert_allclose(last_point.ground_distance, 500000.0)
        assert_allclose(last_point.altitude, 10000.0)
        assert_allclose(last_point.time, 12141.0, rtol=1e-2)
        assert_allclose(last_point.true_airspeed, 233.6, atol=0.1)
        assert_allclose(last_point.mass, 69568.0, rtol=1e-4)
        assert last_point.engine_setting == EngineSetting.CRUISE

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_optimal_cruise(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = OptimalCruiseSegment(
        target=FlightPoint(ground_distance=5.0e5),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CRUISE,
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(mass=70000.0, time=1000.0, ground_distance=1e5, mach=0.78)
        )

        first_point = flight_points.iloc[0]
        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.05s as time step
        assert_allclose(first_point.altitude, 9156.0, atol=1.0)
        assert_allclose(first_point.true_airspeed, 236.4, atol=0.1)
        assert_allclose(first_point.CL, polar.optimal_cl)
        assert_allclose(first_point.CL, polar.optimal_cl)
        assert first_point.engine_setting == EngineSetting.CRUISE

        assert_allclose(last_point.ground_distance, 600000.0)
        assert_allclose(last_point.CL, polar.optimal_cl)
        assert_allclose(last_point.altitude, 9196.0, atol=1.0)
        assert_allclose(last_point.time, 3115.0, rtol=1e-2)
        assert_allclose(last_point.true_airspeed, 236.3, atol=0.1)
        assert_allclose(last_point.mass, 69577.0, rtol=1e-4)
        assert last_point.engine_setting == EngineSetting.CRUISE

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_and_cruise_at_optimal_flight_level(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 3.0e-5), 2)
    reference_area = 120.0

    segment = ClimbAndCruiseSegment(
        target=FlightPoint(
            ground_distance=10.0e6, altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL
        ),
        propulsion=propulsion,
        reference_area=reference_area,
        polar=polar,
        engine_setting=EngineSetting.CRUISE,
        climb_segment=AltitudeChangeSegment(
            target=FlightPoint(),
            propulsion=propulsion,
            reference_area=reference_area,
            polar=polar,
            thrust_rate=0.9,
            engine_setting=EngineSetting.CLIMB,
        ),
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(mass=70000.0, altitude=8000.0, mach=0.78, ground_distance=1.0e6)
        )

        first_point = flight_points.iloc[0]
        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 1.0s as time step

        assert_allclose(first_point.altitude, 8000.0)
        assert_allclose(first_point.thrust_rate, 0.9)
        assert_allclose(first_point.true_airspeed, 240.3, atol=0.1)
        assert first_point.engine_setting == EngineSetting.CLIMB

        assert_allclose(flight_points.mach, 0.78)
        assert_allclose(last_point.ground_distance, 11.0e6)
        assert_allclose(last_point.altitude, 9753.6)
        assert_allclose(last_point.time, 42659.0, rtol=1e-3)
        assert_allclose(last_point.true_airspeed, 234.4, atol=0.1)
        assert_allclose(last_point.mass, 48874.0, rtol=1e-4)
        assert last_point.engine_setting == EngineSetting.CRUISE

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_and_cruise_at_optimal_flight_level_with_unpickable(polar, tmp_path):
    # Create temporary folder containing a dummy data file
    d = tmp_path / "sub"
    d.mkdir()
    file = d / "data.txt"
    with open(file, "w") as f:
        f.write("This is a test file for unpickable propulsion test.")

    # Actually try to run the cruise segment
    engine = DummyUnpickableEngine(0.5e5, 3.0e-5, file)
    propulsion = FuelEngineSet(engine, 2)
    reference_area = 120.0
    try:
        segment = ClimbAndCruiseSegment(
            target=FlightPoint(
                ground_distance=10.0e6, altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL
            ),
            propulsion=propulsion,
            reference_area=reference_area,
            polar=polar,
            engine_setting=EngineSetting.CRUISE,
            climb_segment=AltitudeChangeSegment(
                target=FlightPoint(),
                propulsion=propulsion,
                reference_area=reference_area,
                polar=polar,
                thrust_rate=0.9,
                engine_setting=EngineSetting.CLIMB,
            ),
        )
    except TypeError:
        engine.close_file()
        pytest.fail("Unpickable propulsion incorrectly handled")

    def run():
        flight_points = segment.compute_from(
            FlightPoint(mass=70000.0, altitude=8000.0, mach=0.78, ground_distance=1.0e6)
        )

        first_point = flight_points.iloc[0]
        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 1.0s as time step

        assert_allclose(first_point.altitude, 8000.0)
        assert_allclose(first_point.thrust_rate, 0.9)
        assert_allclose(first_point.true_airspeed, 240.3, atol=0.1)
        assert first_point.engine_setting == EngineSetting.CLIMB

        assert_allclose(flight_points.mach, 0.78)
        assert_allclose(last_point.ground_distance, 11.0e6)
        assert_allclose(last_point.altitude, 9753.6)
        assert_allclose(last_point.time, 42659.0, rtol=1e-3)
        assert_allclose(last_point.true_airspeed, 234.4, atol=0.1)
        assert_allclose(last_point.mass, 48874.0, rtol=1e-4)
        assert last_point.engine_setting == EngineSetting.CRUISE

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_and_cruise_at_optimal_flight_level_with_capped_flight_level(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 3.0e-5), 2)
    reference_area = 120.0

    segment = ClimbAndCruiseSegment(
        target=FlightPoint(
            ground_distance=10.0e6, altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL
        ),
        propulsion=propulsion,
        reference_area=reference_area,
        polar=polar,
        climb_segment=AltitudeChangeSegment(
            target=FlightPoint(),
            propulsion=propulsion,
            reference_area=reference_area,
            polar=polar,
            thrust_rate=0.9,
        ),
        maximum_flight_level=300.0,
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(mass=70000.0, altitude=8000.0, mach=0.78, ground_distance=1.0e6)
        )

        first_point = flight_points.iloc[0]
        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 1.0s as time step

        assert_allclose(first_point.altitude, 8000.0)
        assert_allclose(first_point.thrust_rate, 0.9)
        assert_allclose(first_point.true_airspeed, 240.3, atol=0.1)

        assert_allclose(flight_points.mach, 0.78)
        assert_allclose(last_point.ground_distance, 11.0e6)
        assert_allclose(last_point.altitude, 9144.0)
        assert_allclose(last_point.time, 42287.0, rtol=1e-3)
        assert_allclose(last_point.true_airspeed, 236.5, atol=0.1)
        assert_allclose(last_point.mass, 48807.0, rtol=1e-4)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_and_cruise_at_optimal_flight_level_with_start_at_exact_flight_level(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 3.0e-5), 2)
    reference_area = 120.0

    segment = ClimbAndCruiseSegment(
        target=FlightPoint(
            ground_distance=10.0e6, altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL
        ),
        propulsion=propulsion,
        reference_area=reference_area,
        polar=polar,
        climb_segment=AltitudeChangeSegment(
            target=FlightPoint(),
            propulsion=propulsion,
            reference_area=reference_area,
            polar=polar,
            thrust_rate=0.9,
        ),
    )

    def run():
        # Start at exact optimum flight level ======================================================
        flight_points = segment.compute_from(FlightPoint(mass=70000.0, altitude=9753.6, mach=0.78))

        first_point = flight_points.iloc[0]
        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 1.0s as time step

        assert_allclose(first_point.altitude, 9753.6)
        assert_allclose(first_point.thrust_rate, 0.9)
        assert_allclose(first_point.true_airspeed, 234.4, atol=0.1)

        assert_allclose(flight_points.mach, 0.78)
        assert_allclose(last_point.altitude, 9753.6)
        assert_allclose(last_point.ground_distance, 10.0e6)
        assert_allclose(last_point.time, 42659.0, rtol=1e-3)
        assert_allclose(last_point.true_airspeed, 234.4, atol=0.1)
        assert_allclose(last_point.mass, 48987.0, rtol=1e-4)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()
