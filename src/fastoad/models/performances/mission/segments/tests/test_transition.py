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

from fastoad.model_base import FlightPoint
from ..base import RELATIVE_FIELD_FLAG
from ..transition import DummyTakeoffSegment, DummyTransitionSegment


def test_dummy_takeoff():
    dummy_takeoff = DummyTakeoffSegment(
        target=FlightPoint(
            time=45,
            true_airspeed=50.0,
            mass=-100 + RELATIVE_FIELD_FLAG,
            altitude=10 + RELATIVE_FIELD_FLAG,
        )
    )

    flight_points = dummy_takeoff.compute_from(
        FlightPoint(time=500, altitude=0.0, mass=50000, mach=0.0, ground_distance=100.0e3)
    )

    assert_allclose(flight_points.time, [500, 545])
    assert_allclose(flight_points.mass, [50000, 49900])
    assert_allclose(flight_points.altitude, [0.0, 10.0])
    assert_allclose(flight_points.ground_distance, [100.0e3, 100.0e3])
    assert_allclose(flight_points.true_airspeed, [0.0, 50.0])
    assert_allclose(flight_points.mach, [0.0, 0.1469], rtol=1.0e-3)


def test_dummy_climb():
    dummy_climb = DummyTransitionSegment(
        target=FlightPoint(altitude=9.0e3, mach=0.8, ground_distance=400.0e3), mass_ratio=0.8
    )

    flight_points = dummy_climb.compute_from(
        FlightPoint(altitude=0.0, mass=100.0e3, mach=0.0, ground_distance=100.0e3)
    )

    assert_allclose(flight_points.mass, [100.0e3, 80.0e3])
    assert_allclose(flight_points.altitude, [0.0, 9.0e3])
    assert_allclose(flight_points.ground_distance, [100.0e3, 500.0e3])
    assert_allclose(flight_points.mach, [0.0, 0.8])
    assert_allclose(flight_points.true_airspeed, [0.0, 243.04], rtol=1.0e-4)


def test_dummy_descent_with_reserve():
    dummy_descent_reserve = DummyTransitionSegment(
        target=FlightPoint(altitude=0.0, mach=0.0, ground_distance=500.0e3),
        mass_ratio=0.9,
        reserve_mass_ratio=0.08,
    )
    flight_points = dummy_descent_reserve.compute_from(
        FlightPoint(altitude=9.0e3, mass=60.0e3, mach=0.8)
    )
    assert_allclose(flight_points.mass, [60.0e3, 54.0e3, 50.0e3])
    assert_allclose(flight_points.altitude, [9.0e3, 0.0, 0.0])
    assert_allclose(flight_points.ground_distance, [0.0, 500.0e3, 500.0e3])
    assert_allclose(flight_points.mach, [0.8, 0.0, 0.0])
    assert_allclose(flight_points.true_airspeed, [243.04, 0.0, 0.0], rtol=1.0e-4)


def test_dummy_reserve():
    dummy_reserve = DummyTransitionSegment(
        target=FlightPoint(altitude=0.0, mach=0.0), reserve_mass_ratio=0.1
    )
    flight_points = dummy_reserve.compute_from(FlightPoint(altitude=0.0, mach=0.0, mass=55.0e3))
    assert_allclose(flight_points.mass, [55.0e3, 55.0e3, 50.0e3])
    assert_allclose(flight_points.altitude, [0.0, 0.0, 0.0])
    assert_allclose(flight_points.ground_distance, [0.0, 0.0, 0.0])
    assert_allclose(flight_points.mach, [0.0, 0.0, 0.0])
    assert_allclose(flight_points.true_airspeed, [0.0, 0.0, 0.0], rtol=1.0e-4)
