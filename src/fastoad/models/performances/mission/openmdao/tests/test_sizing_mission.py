#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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
import pytest
from matplotlib.ticker import MultipleLocator
from scipy.constants import foot, knot

from fastoad.io import VariableIO
from tests.testing_utilities import run_system
from ..sizing_mission import SizingMission

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    mkdir(RESULTS_FOLDER_PATH)


def plot_flight(flight_points, fig_filename):
    plt.figure(figsize=(12, 12))
    ax1 = plt.subplot(2, 1, 1)
    plt.plot(flight_points.ground_distance / 1000.0, flight_points.altitude / foot, "o-")
    plt.xlabel("distance [km]")
    plt.ylabel("altitude [ft]")
    ax1.xaxis.set_minor_locator(MultipleLocator(50))
    ax1.yaxis.set_minor_locator(MultipleLocator(500))
    plt.grid(which="major", color="k")
    plt.grid(which="minor")

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
    ax2.xaxis.set_minor_locator(MultipleLocator(50))
    ax2.yaxis.set_minor_locator(MultipleLocator(5))
    plt.grid(which="major", color="k")
    plt.grid(which="minor")

    plt.twinx(ax2)
    lines += plt.plot(
        flight_points.ground_distance / 1000.0, flight_points.mach, "r.-", label="Mach"
    )
    plt.ylabel("Mach")

    labels = [l.get_label() for l in lines]
    plt.legend(lines, labels, loc=0)

    plt.savefig(pth.join(RESULTS_FOLDER_PATH, fig_filename))
    plt.close()


def test_sizing_mission(cleanup):
    input_file_path = pth.join(DATA_FOLDER_PATH, "mission_inputs.xml")
    ivc = VariableIO(input_file_path).read().to_ivc()

    problem = run_system(
        SizingMission(
            propulsion_id="fastoad.wrapper.propulsion.rubber_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "flight_points.csv"),
        ),
        ivc,
    )
    plot_flight(problem.model.component.flight_points, "flight.png")
