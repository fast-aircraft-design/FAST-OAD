"""Tests module for routes.py"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

import shutil
from pathlib import Path

import pytest
from numpy.testing import assert_allclose
from scipy.constants import foot, knot

from fastoad.constants import EngineSetting, FlightPhase
from fastoad.model_base import FlightPoint

from .conftest import ClimbPhase, DescentPhase, InitialClimbPhase
from ..routes import RangedRoute
from ..segments.registered.cruise import CruiseSegment

RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_ranged_route(low_speed_polar, high_speed_polar, propulsion, cleanup):
    total_distance = 2.0e6

    kwargs = dict(propulsion=propulsion, reference_area=120.0)
    initial_climb = InitialClimbPhase(
        **kwargs, polar=low_speed_polar, thrust_rate=1.0, name="initial_climb", time_step=0.2
    )
    climb = ClimbPhase(
        **kwargs,
        polar=high_speed_polar,
        thrust_rate=0.8,
        target_altitude="mach",
        maximum_mach=0.78,
        name="climb",
        time_step=5.0,
    )
    cruise = CruiseSegment(
        **kwargs,
        target=FlightPoint(ground_distance=0.0),
        polar=high_speed_polar,
        engine_setting=EngineSetting.CRUISE,
        name=FlightPhase.CRUISE.value,
    )
    descent = DescentPhase(
        **kwargs,
        polar=high_speed_polar,
        thrust_rate=0.05,
        target_altitude=1500.0 * foot,
        name=FlightPhase.DESCENT.value,
        time_step=5.0,
    )

    flight_calculator = RangedRoute(
        climb_phases=[initial_climb, climb],
        cruise_segment=cruise,
        descent_phases=[descent],
        flight_distance=total_distance,
    )
    assert flight_calculator.cruise_speed == ("mach", 0.78)

    start = FlightPoint(
        true_airspeed=150.0 * knot, altitude=100.0 * foot, mass=70000.0, ground_distance=100000.0
    )
    flight_points = flight_calculator.compute_from(start)

    # plot_flight(flight_points, "test_ranged_flight.png", RESULTS_FOLDER_PATH)

    assert_allclose(
        flight_points.iloc[-1].ground_distance,
        total_distance + start.ground_distance,
        atol=flight_calculator.distance_accuracy,
    )
