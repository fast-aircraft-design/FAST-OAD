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
import pandas as pd
import pytest
from numpy.testing import assert_allclose
from scipy.constants import foot

from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import AbstractFuelPropulsion, FuelEngineSet
from ..altitude_change import AltitudeChangeSegment
from ..cruise import (
    BreguetCruiseSegment,
    ClimbAndCruiseSegment,
    CruiseSegment,
    OptimalCruiseSegment,
)
from ..hold import HoldSegment
from ..speed_change import SpeedChangeSegment
from ..taxi import TaxiSegment
from ..transition import DummyTransitionSegment
from ...polar import Polar


def print_dataframe(df):
    """Utility for correctly printing results"""
    # Not used if all goes all well. Please keep it for future test setting/debugging.
    with pd.option_context(
        "display.max_rows", 20, "display.max_columns", None, "display.width", None
    ):
        print()
        print(df)


class DummyEngine(AbstractFuelPropulsion):
    def __init__(self, max_thrust, max_sfc):
        """
        Dummy engine model.

        Max thrust does not depend on flight conditions.
        SFC varies linearly with thrust_rate, from max_sfc/2. at thrust rate is 0.,
        to max_sfc when thrust_rate is 1.0

        :param max_thrust: thrust when thrust rate = 1.0
        :param max_sfc: SFC when thrust rate = 1.0
        """
        self.max_thrust = max_thrust
        self.max_sfc = max_sfc

    def compute_flight_points(self, flight_point: FlightPoint):

        if flight_point.thrust_is_regulated or flight_point.thrust_rate is None:
            flight_point.thrust_rate = flight_point.thrust / self.max_thrust
        else:
            flight_point.thrust = self.max_thrust * flight_point.thrust_rate

        flight_point.sfc = self.max_sfc * (1.0 + flight_point.thrust_rate) / 2.0


@pytest.fixture
def polar() -> Polar:
    """Returns a dummy polar where max L/D ratio is around 16."""
    cl = np.arange(0.0, 1.5, 0.01)
    cd = 0.5e-1 * cl ** 2 + 0.01
    return Polar(cl, cd)


def test_climb_fixed_altitude_at_constant_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=10000.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
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


def test_climb_fixed_altitude_at_constant_EAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    flight_points = AltitudeChangeSegment(
        target=FlightPoint(altitude=10000.0, equivalent_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
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
    ).compute_from(FlightPoint(altitude=5000.0, true_airspeed=250.0, mass=70000.0),)

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
    ).compute_from(FlightPoint(altitude=5000.0, true_airspeed=250.0, mass=70000.0),)

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
    ).compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0),)

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
    ).compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0),)

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
        len(segment.compute_from(FlightPoint(altitude=5000.0, true_airspeed=150.0, mass=70000.0),))
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
        FlightPoint(altitude=10000.0, true_airspeed=200.0, mass=70000.0, time=2000.0),
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
    ).compute_from(FlightPoint(altitude=10000.0, equivalent_airspeed=200.0, mass=70000.0),)

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
    ).compute_from(FlightPoint(altitude=10000.0, mass=70000.0, mach=0.78),)

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.equivalent_airspeed, 150.0)
    assert_allclose(last_point.mach, 0.78)
    assert_allclose(last_point.time, 343.6, rtol=1e-2)
    assert_allclose(last_point.altitude, 8654.0, atol=1.0)
    assert_allclose(last_point.true_airspeed, 238.1, atol=0.1)
    assert_allclose(last_point.mass, 69962.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 81042.0, rtol=1e-3)


def test_acceleration_to_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = SpeedChangeSegment(
        target=FlightPoint(true_airspeed=250.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=0.2,
    )
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


def test_acceleration_to_EAS(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    flight_points = SpeedChangeSegment(
        target=FlightPoint(equivalent_airspeed=250.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=0.2,
    ).compute_from(FlightPoint(altitude=1000.0, true_airspeed=150.0, mass=70000.0))

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.time, 128.2, rtol=1e-2)
    assert_allclose(last_point.altitude, 1000.0)
    assert_allclose(last_point.true_airspeed, 262.4, atol=1e-1)
    assert_allclose(last_point.mass, 69872.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 26868.0, rtol=1e-3)


def test_acceleration_to_mach(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    flight_points = SpeedChangeSegment(
        target=FlightPoint(mach=0.8),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=0.2,
    ).compute_from(FlightPoint(altitude=1000.0, true_airspeed=150.0, mass=70000.0))

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.time, 138.0, rtol=1e-2)
    assert_allclose(last_point.altitude, 1000.0)
    assert_allclose(last_point.mach, 0.8, atol=1e-5)
    assert_allclose(last_point.mass, 69862.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 29470.0, rtol=1e-3)


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
        segment.compute_from(FlightPoint(altitude=5000.0, true_airspeed=150.0, mass=70000.0),)
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
    flight_points = segment.compute_from(
        FlightPoint(altitude=5000.0, true_airspeed=250.0, mass=70000.0),
    )

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.time, 315.8, rtol=1e-2)
    assert_allclose(last_point.altitude, 5000.0)
    assert_allclose(last_point.true_airspeed, 150.0)
    assert_allclose(last_point.mass, 69982.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 62804.0, rtol=1e-3)


def test_cruise_at_constant_altitude(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = CruiseSegment(
        target=FlightPoint(ground_distance=5.0e5),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
    )
    flight_points = segment.compute_from(FlightPoint(mass=70000.0, altitude=10000.0, mach=0.78))

    first_point = flight_points.iloc[0]
    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.05s as time step
    assert_allclose(first_point.altitude, 10000.0)
    assert_allclose(first_point.true_airspeed, 233.6, atol=0.1)

    assert_allclose(last_point.ground_distance, 500000.0)
    assert_allclose(last_point.altitude, 10000.0)
    assert_allclose(last_point.time, 2141.0, rtol=1e-2)
    assert_allclose(last_point.true_airspeed, 233.6, atol=0.1)
    assert_allclose(last_point.mass, 69568.0, rtol=1e-4)


def test_breguet_cruise(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = BreguetCruiseSegment(
        target=FlightPoint(ground_distance=5.0e5),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
    )
    flight_points = segment.compute_from(
        FlightPoint(time=10000.0, mass=70000.0, altitude=10000.0, mach=0.78)
    )

    print_dataframe(flight_points)

    first_point = flight_points.iloc[0]
    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with CruiseSegment and 0.05s as
    # time step
    assert_allclose(first_point.altitude, 10000.0)
    assert_allclose(first_point.true_airspeed, 233.6, atol=0.1)

    assert_allclose(last_point.ground_distance, 500000.0)
    assert_allclose(last_point.altitude, 10000.0)
    assert_allclose(last_point.time, 12141.0, rtol=1e-2)
    assert_allclose(last_point.true_airspeed, 233.6, atol=0.1)
    assert_allclose(last_point.mass, 69568.0, rtol=1e-4)


def test_optimal_cruise(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = OptimalCruiseSegment(
        target=FlightPoint(ground_distance=5.0e5),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
    )
    flight_points = segment.compute_from(
        FlightPoint(mass=70000.0, time=1000.0, ground_distance=1e5, mach=0.78),
    )
    print_dataframe(flight_points)

    first_point = flight_points.iloc[0]
    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.05s as time step
    assert_allclose(first_point.altitude, 9156.0, atol=1.0)
    assert_allclose(first_point.true_airspeed, 236.4, atol=0.1)
    assert_allclose(first_point.CL, polar.optimal_cl)

    assert_allclose(last_point.ground_distance, 600000.0)
    assert_allclose(last_point.CL, polar.optimal_cl)
    assert_allclose(last_point.altitude, 9196.0, atol=1.0)
    assert_allclose(last_point.time, 3115.0, rtol=1e-2)
    assert_allclose(last_point.true_airspeed, 236.3, atol=0.1)
    assert_allclose(last_point.mass, 69577.0, rtol=1e-4)


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
        climb_segment=AltitudeChangeSegment(
            target=FlightPoint(),
            propulsion=propulsion,
            reference_area=reference_area,
            polar=polar,
            thrust_rate=0.9,
        ),
    )

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
    assert_allclose(last_point.altitude, 9753.6)
    assert_allclose(last_point.ground_distance, 11.0e6)
    assert_allclose(last_point.time, 42659.0, rtol=1e-3)
    assert_allclose(last_point.true_airspeed, 234.4, atol=0.1)
    assert_allclose(last_point.mass, 48874.0, rtol=1e-4)


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
    assert_allclose(last_point.altitude, 9144.0)
    assert_allclose(last_point.ground_distance, 11.0e6)
    assert_allclose(last_point.time, 42287.0, rtol=1e-3)
    assert_allclose(last_point.true_airspeed, 236.5, atol=0.1)
    assert_allclose(last_point.mass, 48807.0, rtol=1e-4)


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

    # Start at exact optimum flight level ==========================================================
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


def test_taxi():
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = TaxiSegment(target=FlightPoint(time=500.0), propulsion=propulsion, thrust_rate=0.1)
    flight_points = segment.compute_from(
        FlightPoint(altitude=10.0, true_airspeed=10.0, mass=50000.0, time=10000.0),
    )

    last_point = flight_points.iloc[-1]
    assert_allclose(last_point.altitude, 10.0, atol=1.0)
    assert_allclose(last_point.time, 10500.0, rtol=1e-2)
    assert_allclose(last_point.true_airspeed, 10.0, atol=0.1)
    assert_allclose(last_point.mass, 49973.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 5000.0)


def test_hold(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 2.0e-5), 2)

    segment = HoldSegment(
        target=FlightPoint(time=3000.0), propulsion=propulsion, reference_area=120.0, polar=polar
    )
    flight_points = segment.compute_from(
        FlightPoint(altitude=500.0, equivalent_airspeed=250.0, mass=60000.0),
    )

    last_point = flight_points.iloc[-1]
    assert_allclose(last_point.time, 3000.0)
    assert_allclose(last_point.altitude, 500.0)
    assert_allclose(last_point.equivalent_airspeed, 250.0, atol=0.1)
    assert_allclose(last_point.mass, 57776.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 768323.0, rtol=1.0e-3)


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
        target=FlightPoint(altitude=0.0, mach=0.0), reserve_mass_ratio=0.1,
    )
    flight_points = dummy_reserve.compute_from(FlightPoint(altitude=0.0, mach=0.0, mass=55.0e3))
    assert_allclose(flight_points.mass, [55.0e3, 55.0e3, 50.0e3])
    assert_allclose(flight_points.altitude, [0.0, 0.0, 0.0])
    assert_allclose(flight_points.ground_distance, [0.0, 0.0, 0.0])
    assert_allclose(flight_points.mach, [0.0, 0.0, 0.0])
    assert_allclose(flight_points.true_airspeed, [0.0, 0.0, 0.0], rtol=1.0e-4)
