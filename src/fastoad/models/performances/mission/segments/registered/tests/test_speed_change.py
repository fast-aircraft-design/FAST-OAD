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

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet

from .conftest import DummyEngine
from ..speed_change import SpeedChangeSegment


def test_acceleration_to_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = SpeedChangeSegment(
        target=FlightPoint(true_airspeed=250.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=0.2,
        engine_setting=EngineSetting.CLIMB,  # The engine model does not use this setting
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=5000.0, true_airspeed=150.0, mass=70000.0)
        )

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.time, 103.3, rtol=1e-2)
        assert_allclose(last_point.altitude, 5000.0)
        assert_allclose(last_point.true_airspeed, 250.0)
        assert_allclose(last_point.mass, 69896.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 20697.0, rtol=1e-3)
        assert last_point.engine_setting == EngineSetting.CLIMB

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_acceleration_to_EAS(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = SpeedChangeSegment(
        target=FlightPoint(equivalent_airspeed=250.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=0.2,
        engine_setting=EngineSetting.CRUISE,  # The engine model does not use this setting
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=1000.0, true_airspeed=150.0, mass=70000.0)
        )

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.time, 128.2, rtol=1e-2)
        assert_allclose(last_point.altitude, 1000.0)
        assert_allclose(last_point.true_airspeed, 262.4, atol=1e-1)
        assert_allclose(last_point.mass, 69872.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 26868.0, rtol=1e-3)
        assert last_point.engine_setting == EngineSetting.CRUISE

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_acceleration_to_mach(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = SpeedChangeSegment(
        target=FlightPoint(mach=0.8),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=0.2,
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=1000.0, true_airspeed=150.0, mass=70000.0)
        )

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.time, 138.0, rtol=1e-2)
        assert_allclose(last_point.altitude, 1000.0)
        assert_allclose(last_point.mach, 0.8, atol=1e-5)
        assert_allclose(last_point.mass, 69862.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 29470.0, rtol=1e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_acceleration_not_enough_thrust(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = SpeedChangeSegment(
        target=FlightPoint(true_airspeed=250.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=0.1,
    )
    assert len(
        segment.compute_from(FlightPoint(altitude=5000.0, true_airspeed=150.0, mass=70000.0))
    )


def test_deceleration_not_enough_thrust(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = SpeedChangeSegment(
        target=FlightPoint(true_airspeed=150.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=0.1,
        time_step=1.0,
    )
    segment.time_step = 1.0

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=5000.0, true_airspeed=250.0, mass=70000.0)
        )

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.time, 315.8, rtol=1e-2)
        assert_allclose(last_point.altitude, 5000.0)
        assert_allclose(last_point.true_airspeed, 150.0)
        assert_allclose(last_point.mass, 69982.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 62804.0, rtol=1e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()
