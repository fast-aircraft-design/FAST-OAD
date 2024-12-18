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

import numpy as np
import pytest
from numpy.testing import assert_allclose
from pandas._testing import assert_frame_equal

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import AbstractFuelPropulsion, FuelEngineSet

from ..ground_speed_change import GroundSpeedChangeSegment
from ..takeoff.end_of_takeoff import EndOfTakeoffSegment
from ..takeoff.rotation import RotationSegment
from ..takeoff.takeoff import TakeOffSequence
from ....base import FlightSequence
from ....polar import Polar
from ....polar_modifier import AbstractPolarModifier, GroundEffectRaymer


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
    cl = np.arange(0.0, 1.5, 0.01) + 0.5
    cd = 0.5e-1 * cl**2 + 0.01
    alpha = np.linspace(-2.2918311, 14.7823111, 150) / 180 * np.pi

    return Polar(cl, cd, alpha)


@pytest.fixture
def polar_modifier() -> AbstractPolarModifier:
    span = 34.5
    landing_gear_height = 2.5
    induced_drag_coef = 0.034
    k_cd = 1.0
    k_winglet = 1.0

    return GroundEffectRaymer(span, landing_gear_height, induced_drag_coef, k_winglet, k_cd)


def test_ground_speed_change(polar, polar_modifier):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = GroundSpeedChangeSegment(
        target=FlightPoint(true_airspeed=75.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        polar_modifier=polar_modifier,
        engine_setting=EngineSetting.CLIMB,
    )
    segment.thrust_rate = 1.0
    segment.time_step = 0.2
    flight_points = segment.compute_from(FlightPoint(altitude=0.0, mass=70000.0, true_airspeed=0.0))

    last_point = flight_points.iloc[-1]
    assert_allclose(last_point.altitude, 0.0)
    assert_allclose(last_point.true_airspeed, 75.0)
    assert_allclose(last_point.time, 29.44, rtol=1e-2)
    assert_allclose(last_point.mass, 69936.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 1100, rtol=1e-3)
    assert last_point.engine_setting == EngineSetting.CLIMB


def test_rotation(polar, polar_modifier):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = RotationSegment(
        target=FlightPoint(),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        polar_modifier=polar_modifier,
        engine_setting=EngineSetting.CLIMB,
    )
    segment.thrust_rate = 1.0
    flight_points = segment.compute_from(
        FlightPoint(time=30.0, altitude=0.0, mass=70000.0, true_airspeed=75.0, alpha=0.0)
    )  # Test with dict

    last_point = flight_points.iloc[-1]
    assert_allclose(last_point.altitude, 0.0)
    assert_allclose(last_point.true_airspeed, 81.22, rtol=1e-3)
    assert_allclose(last_point.time, 32.58, rtol=1e-2)
    assert_allclose(last_point.mass, 69995.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 200.64, rtol=1e-3)
    assert_allclose(np.degrees(last_point.alpha), 7.713, rtol=1e-3)
    assert last_point.engine_setting == EngineSetting.CLIMB


def test_end_of_takeoff(polar, polar_modifier):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = EndOfTakeoffSegment(
        target=FlightPoint(altitude=12.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        polar_modifier=polar_modifier,
        engine_setting=EngineSetting.CLIMB,
    )
    segment.thrust_rate = 1.0
    segment.time_step = 0.05
    flight_points = segment.compute_from(
        FlightPoint(
            time=35.0,
            altitude=0.0,
            mass=70000.0,
            true_airspeed=85.0,
            alpha=10.0 / 180 * 3.14,
            slope_angle=0.0,
        )
    )  # Test with dict

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.05s as time step
    assert_allclose(last_point.altitude, 12.0)
    assert_allclose(last_point.true_airspeed, 90.88, rtol=1e-3)
    assert_allclose(last_point.time, 38.46, rtol=1e-2)
    assert_allclose(last_point.mass, 69993.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 302.97, rtol=1e-3)
    assert_allclose(last_point.alpha, 0.105, rtol=1e-2)
    assert_allclose(last_point.slope_angle, 0.06907, rtol=1e-3)
    assert_allclose(last_point.slope_angle_derivative, 0.01251, rtol=1e-3)
    assert last_point.engine_setting == EngineSetting.CLIMB


def test_takeoff(polar, polar_modifier):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    ground_segment = GroundSpeedChangeSegment(
        target=FlightPoint(equivalent_airspeed=75.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        polar_modifier=polar_modifier,
        engine_setting=EngineSetting.CLIMB,
        thrust_rate=1.0,
        time_step=0.2,
    )
    rotation_segment = RotationSegment(
        target=FlightPoint(),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        polar_modifier=polar_modifier,
        engine_setting=EngineSetting.CLIMB,
        thrust_rate=1.0,
        rotation_rate=0.05,
        alpha_limit=0.1,
        time_step=0.2,
    )
    end_segment = EndOfTakeoffSegment(
        target=FlightPoint(altitude=12.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        polar_modifier=polar_modifier,
        engine_setting=EngineSetting.CLIMB,
        thrust_rate=1.0,
        time_step=0.05,
    )
    sequence = FlightSequence()
    [sequence.append(seg) for seg in [ground_segment, rotation_segment, end_segment]]

    segment_1 = TakeOffSequence(
        target=FlightPoint(altitude=12.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        polar_modifier=polar_modifier,
        # engine_setting=EngineSetting.CLIMB,   # using default value
        rotation_equivalent_airspeed=75.0,
        rotation_rate=0.05,
        rotation_alpha_limit=0.1,
        # thrust_rate=1.0,                      # using default value
        time_step=0.2,
    )

    start_point = FlightPoint(altitude=0.0, mass=70000.0, true_airspeed=0.0)

    ref_flight_points = sequence.compute_from(start_point)
    flight_points_1 = segment_1.compute_from(start_point)
    assert_frame_equal(flight_points_1, ref_flight_points, rtol=1e-6)

    # for segment 2, field values are modified afterward.
    segment_2 = TakeOffSequence(
        target=FlightPoint(),
        propulsion=None,
        reference_area=0.0,
        polar=None,
        polar_modifier=None,
        engine_setting=None,
        rotation_equivalent_airspeed=0.0,
        thrust_rate=0.0,
        time_step=0.0,
    )
    segment_2.target = FlightPoint(altitude=12.0)
    segment_2.propulsion = propulsion
    segment_2.reference_area = 120.0
    segment_2.polar = polar
    segment_2.polar_modifier = polar_modifier
    segment_2.engine_setting = EngineSetting.CLIMB
    segment_2.rotation_equivalent_airspeed = 75.0
    segment_2.rotation_rate = 0.05
    segment_2.rotation_alpha_limit = 0.1
    segment_2.thrust_rate = 1.0
    segment_2.time_step = 0.2

    flight_points_2 = segment_2.compute_from(start_point)
    assert_frame_equal(flight_points_2, ref_flight_points, rtol=1e-6)
