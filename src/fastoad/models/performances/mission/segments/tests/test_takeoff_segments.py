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

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import AbstractFuelPropulsion, FuelEngineSet
from ..end_of_takeoff import EndOfTakoffSegment
from ..ground_speed_change import GroundSpeedChangeSegment
from ..rotation import RotationSegment
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
    cl = np.arange(0.0, 1.5, 0.01) + 0.5
    polar_dict = {
        "CL": cl,
        "CD": 0.5e-1 * cl ** 2 + 0.01,
        "ground_effect": "Raymer",
        "span": 34.5,
        "lg_height": 2.5,
        "induced_drag_coef": 0.034,
        "k_cd": 1.0,
        "k_winglet": 1.0,
        "CL_alpha": 5.0,
        "CL0_clean": 0.2,
        "CL_high_lift": 0.5,
    }
    return Polar(polar_dict)


def test_ground_speed_change(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = GroundSpeedChangeSegment(
        target=FlightPoint(true_airspeed=75.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
    )
    segment.thrust_rate = 1.0
    segment.time_step = 0.2
    flight_points = segment.compute_from(
        FlightPoint(altitude=0.0, mass=70000.0, true_airspeed=0.0)
    )  # Test with dict

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.altitude, 0.0)
    assert_allclose(last_point.true_airspeed, 75.0)
    assert_allclose(last_point.time, 29.44, rtol=1e-2)
    assert_allclose(last_point.mass, 69936.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 1100, rtol=1e-3)
    assert last_point.engine_setting == EngineSetting.CLIMB


def test_rotation(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = RotationSegment(
        target=FlightPoint(altitude=12.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
    )
    segment.thrust_rate = 1.0
    flight_points = segment.compute_from(
        FlightPoint(time=30.0, altitude=0.0, mass=70000.0, true_airspeed=75.0, alpha=0.0)
    )  # Test with dict

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.altitude, 0.0)
    assert_allclose(last_point.true_airspeed, 81.22, rtol=1e-3)
    assert_allclose(last_point.time, 32.58, rtol=1e-2)
    assert_allclose(last_point.mass, 69995.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 200.25, rtol=1e-3)
    assert last_point.engine_setting == EngineSetting.CLIMB


def test_end_of_takeoff(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = EndOfTakoffSegment(
        target=FlightPoint(altitude=12.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
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
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.altitude, 12.0)
    assert_allclose(last_point.true_airspeed, 90.88, rtol=1e-3)
    assert_allclose(last_point.time, 38.46, rtol=1e-2)
    assert_allclose(last_point.mass, 69993.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 302.97, rtol=1e-3)
    assert last_point.engine_setting == EngineSetting.CLIMB
