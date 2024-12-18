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

from fastoad.model_base import FlightPoint

from ..transition import DummyTransitionSegment


def test_dummy_takeoff():
    target = FlightPoint(
        time=45,
        true_airspeed=50.0,
        mass=-100,
        altitude=10,
    )
    target.set_as_relative(["mass", "altitude"])
    dummy_takeoff = DummyTransitionSegment(target=target)

    def run():
        flight_points = dummy_takeoff.compute_from(
            FlightPoint(
                time=500,
                altitude=0.0,
                mass=50000,
                mach=0.0,
                ground_distance=100.0e3,
                consumed_fuel=300.0,
            )
        )

        assert_allclose(flight_points.time, [500, 545])
        assert_allclose(flight_points.mass, [50000, 49900])
        assert_allclose(flight_points.consumed_fuel, [300.0, 400.0])
        assert_allclose(flight_points.altitude, [0.0, 10.0])
        assert_allclose(flight_points.ground_distance, [100.0e3, 100.0e3])
        assert_allclose(flight_points.true_airspeed, [0.0, 50.0])
        assert_allclose(flight_points.mach, [0.0, 0.1469], rtol=1.0e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_dummy_climb():
    dummy_climb = DummyTransitionSegment(
        target=FlightPoint(altitude=9.0e3, mach=0.8, ground_distance=400.0e3), mass_ratio=0.8
    )

    def run():
        flight_points = dummy_climb.compute_from(
            FlightPoint(altitude=0.0, mass=100.0e3, mach=0.0, ground_distance=100.0e3)
        )

        assert_allclose(flight_points.mass, [100.0e3, 80.0e3])
        assert_allclose(flight_points.altitude, [0.0, 9.0e3])
        assert_allclose(flight_points.ground_distance, [100.0e3, 500.0e3])
        assert_allclose(flight_points.mach, [0.0, 0.8])
        assert_allclose(flight_points.true_airspeed, [0.0, 243.04], rtol=1.0e-4)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_dummy_descent_with_reserve():
    dummy_descent_reserve = DummyTransitionSegment(
        target=FlightPoint(altitude=0.0, mach=0.0, ground_distance=500.0e3),
        mass_ratio=0.9,
        reserve_mass_ratio=0.08,
    )

    def run():
        flight_points = dummy_descent_reserve.compute_from(
            FlightPoint(altitude=9.0e3, mass=60.0e3, mach=0.8)
        )
        assert_allclose(flight_points.mass, [60.0e3, 54.0e3, 50.0e3])
        assert_allclose(flight_points.altitude, [9.0e3, 0.0, 0.0])
        assert_allclose(flight_points.ground_distance, [0.0, 500.0e3, 500.0e3])
        assert_allclose(flight_points.mach, [0.8, 0.0, 0.0])
        assert_allclose(flight_points.true_airspeed, [243.04, 0.0, 0.0], rtol=1.0e-4)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_dummy_reserve():
    dummy_reserve = DummyTransitionSegment(
        target=FlightPoint(altitude=0.0, mach=0.0), reserve_mass_ratio=0.1
    )

    def run():
        flight_points = dummy_reserve.compute_from(FlightPoint(altitude=0.0, mach=0.0, mass=55.0e3))
        assert_allclose(flight_points.mass, [55.0e3, 55.0e3, 50.0e3])
        assert_allclose(flight_points.altitude, [0.0, 0.0, 0.0])
        assert_allclose(flight_points.ground_distance, [0.0, 0.0, 0.0])
        assert_allclose(flight_points.mach, [0.0, 0.0, 0.0])
        assert_allclose(flight_points.true_airspeed, [0.0, 0.0, 0.0], rtol=1.0e-4)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_payload_drop_off():
    target = FlightPoint(
        time=0.0,
        mass=-3000,
        altitude=1,
    )
    target.set_as_relative(["mass", "altitude"])

    segment = DummyTransitionSegment(target=target, fuel_is_consumed=False)

    def run():
        flight_points = segment.compute_from(
            FlightPoint(time=3000.0, altitude=200.0, mach=0.3, mass=55.0e3, consumed_fuel=2500.0)
        )
        assert_allclose(flight_points.time, [3000.0, 3000.0])
        assert_allclose(flight_points.mass, [55000, 52000])
        assert_allclose(flight_points.consumed_fuel, [2500, 2500])
        assert_allclose(flight_points.altitude, [200.0, 201.0])
        assert_allclose(flight_points.mach, [0.3, 0.3], rtol=1e-4)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()
