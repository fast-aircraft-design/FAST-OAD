"""
Tests module for standard_flight.py

These tests use the segment classes and the RubberEngine model, so they are
more integration tests than unit tests.
Therefore, obtained numerical results depend mainly on other classes, so this is
why almost no numerical check is done here (such checks will be done in the
non-regression tests).
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

import os.path as pth
from os import mkdir
from shutil import rmtree

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from fastoad.constants import FlightPhase
from fastoad.models.propulsion import EngineSet
from fastoad.models.propulsion.fuel_propulsion.rubber_engine import RubberEngine
from numpy.testing import assert_allclose
from scipy.constants import knot, foot

from ..standard_flight import StandardFlight
from ...flight.base import RangedFlight
from ...flight_point import FlightPoint
from ...polar import Polar

RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    mkdir(RESULTS_FOLDER_PATH)


def print_dataframe(df):
    """Utility for correctly printing results"""
    # Not used if all goes all well. Please keep it for future test setting/debugging.
    with pd.option_context(
        "display.max_rows", 20, "display.max_columns", None, "display.width", None
    ):
        print()
        print(df)


@pytest.fixture
def high_speed_polar() -> Polar:
    """Returns a dummy polar where max L/D ratio is about 16., around CL=0.5"""
    cl = np.arange(0.0, 1.5, 0.01)
    cd = 0.6e-1 * cl ** 2 + 0.016
    return Polar(cl, cd)


@pytest.fixture
def low_speed_polar() -> Polar:
    """Returns a dummy polar where max L/D ratio is around CL=0.5"""
    cl = np.arange(0.0, 2.0, 0.01)
    cd = 0.6e-1 * cl ** 2 + 0.03
    return Polar(cl, cd)


def plot_flight(flight_points, fig_filename):
    plt.figure(figsize=(12, 12))
    ax1 = plt.subplot(2, 1, 1)
    plt.plot(flight_points.ground_distance / 1000.0, flight_points.altitude / foot, "o-")
    plt.xlabel("distance [km]")
    plt.ylabel("altitude [ft]")
    plt.grid()

    ax2 = plt.subplot(2, 1, 2)
    lines = []
    lines += plt.plot(
        flight_points.ground_distance / 1000.0, flight_points.true_airspeed, "b-", label="TAS [m/s]"
    )
    lines += plt.plot(
        flight_points.ground_distance / 1000.0,
        flight_points.equivalent_airspeed / knot,
        "g--",
        label="EAS [kt]",
    )
    plt.xlabel("distance [km]")
    plt.ylabel("speed")
    plt.grid()

    plt.twinx(ax2)
    lines += plt.plot(
        flight_points.ground_distance / 1000.0, flight_points.mach, "r.-", label="Mach"
    )
    plt.ylabel("Mach")

    labels = [l.get_label() for l in lines]
    plt.legend(lines, labels, loc=0)

    plt.savefig(pth.join(RESULTS_FOLDER_PATH, fig_filename))
    plt.close()


def test_flight(low_speed_polar, high_speed_polar, cleanup):

    engine = RubberEngine(5.0, 30.0, 1500.0, 1.0e5, 0.95, 10000.0)
    propulsion = EngineSet(engine, 2)

    flight_calculator = StandardFlight(
        propulsion=propulsion,
        reference_area=120.0,
        low_speed_climb_polar=low_speed_polar,
        high_speed_polar=high_speed_polar,
        cruise_mach=0.78,
        thrust_rates={FlightPhase.TAKEOFF: 1.0, FlightPhase.CLIMB: 0.93, FlightPhase.DESCENT: 0.2},
        cruise_distance=4.0e6,
        time_step=None,
    )

    flight_points = flight_calculator.compute(
        FlightPoint(true_airspeed=150.0 * knot, altitude=100.0 * foot, mass=70000.0),
    )
    print_dataframe(flight_points)
    plot_flight(flight_points, "test_flight.png")

    end_of_initial_climb = FlightPoint(
        flight_points.loc[flight_points.tag == "End of initial climb"].iloc[0]
    )
    end_of_climb = FlightPoint(flight_points.loc[flight_points.tag == "End of climb"].iloc[0])
    end_of_cruise = FlightPoint(flight_points.loc[flight_points.tag == "End of cruise"].iloc[0])
    end_of_descent = FlightPoint(flight_points.loc[flight_points.tag == "End of descent"].iloc[0])

    assert_allclose(end_of_initial_climb.altitude, 1500 * foot)
    assert_allclose(end_of_initial_climb.equivalent_airspeed, 250 * knot)
    assert_allclose(end_of_climb.mach, 0.78)
    assert end_of_climb.equivalent_airspeed <= 300 * knot
    assert_allclose(end_of_cruise.ground_distance - end_of_climb.ground_distance, 4.0e6)
    assert_allclose(end_of_cruise.mach, 0.78)
    assert_allclose(end_of_descent.altitude, 1500 * foot)
    assert_allclose(end_of_descent.equivalent_airspeed, 250 * knot)


def test_ranged_flight(low_speed_polar, high_speed_polar, cleanup):

    engine = RubberEngine(5.0, 30.0, 1500.0, 1.0e5, 0.95, 10000.0)
    propulsion = EngineSet(engine, 2)

    total_distance = 2.0e6
    flight_calculator = RangedFlight(
        StandardFlight(
            0.0,
            propulsion=propulsion,
            reference_area=120.0,
            low_speed_climb_polar=low_speed_polar,
            high_speed_polar=high_speed_polar,
            cruise_mach=0.78,
            thrust_rates={
                FlightPhase.TAKEOFF: 1.0,
                FlightPhase.CLIMB: 0.93,
                FlightPhase.DESCENT: 0.2,
            },
        ),
        flight_distance=total_distance,
    )

    flight_points = flight_calculator.compute(
        FlightPoint(true_airspeed=150.0 * knot, altitude=100.0 * foot, mass=70000.0),
    )

    plot_flight(flight_points, "test_ranged_flight.png")

    assert_allclose(
        flight_points.iloc[-1].ground_distance,
        total_distance,
        atol=flight_calculator.distance_accuracy,
    )
