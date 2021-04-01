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


import os.path as pth
from os import mkdir
from shutil import rmtree

import matplotlib.pyplot as plt
import pytest
from matplotlib.ticker import MultipleLocator
from numpy.testing import assert_allclose
from openmdao.core.component import Component
from scipy.constants import foot, knot

from fastoad.io import DataFile
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import AbstractFuelPropulsion, IOMPropulsionWrapper, IPropulsion
from fastoad.module_management.service_registry import RegisterPropulsion
from tests.testing_utilities import run_system
from ..mission import Mission, MissionComponent
from ..mission_wrapper import MissionWrapper
from ...mission_definition.exceptions import FastMissionFileMissingMissionNameError

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


# Propulsion definition --------------------------------------------------------
class DummyEngine(AbstractFuelPropulsion):
    def __init__(self, max_thrust, max_sfc):
        """
        Dummy engine model.

        Max thrust does not depend on flight conditions.
        SFC varies linearly with thrust_rate, from max_sfc/2. when thrust rate is 0.,
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


class DummyEngineWrapper(IOMPropulsionWrapper):
    def setup(self, component: Component):
        pass

    @staticmethod
    def get_model(inputs) -> IPropulsion:
        return DummyEngine(1.2e5, 1.5e-5)


# Using the decorator directly on the class would prevent it from being available
# in this file.
RegisterPropulsion("test.wrapper.propulsion.dummy_engine")(DummyEngineWrapper)

# End of propulsion definition -------------------------------------------------


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


def test_mission_component(cleanup):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        MissionComponent(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_mission.csv"),
            use_initializer_iteration=False,
            mission_wrapper=MissionWrapper(pth.join(DATA_FOLDER_PATH, "test_mission.yml")),
            mission_name="operational",
        ),
        ivc,
    )
    # plot_flight(problem.model.component.flight_points, "test_mission.png")
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 6589.0, atol=1.0)


def test_mission_component_breguet(cleanup):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        MissionComponent(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_breguet.csv"),
            use_initializer_iteration=False,
            mission_wrapper=MissionWrapper(pth.join(DATA_FOLDER_PATH, "test_breguet.yml")),
            mission_name="operational",
        ),
        ivc,
    )
    # plot_flight(problem.model.component.flight_points, "test_mission.png")
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 6353.0, atol=1.0)


def test_mission_group_without_loop(cleanup):
    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    ivc = DataFile(input_file_path).to_ivc()

    with pytest.raises(FastMissionFileMissingMissionNameError):
        run_system(
            Mission(
                propulsion_id="test.wrapper.propulsion.dummy_engine",
                out_file=pth.join(RESULTS_FOLDER_PATH, "test_unlooped_mission_group.csv"),
                use_initializer_iteration=False,
                mission_file_path=pth.join(DATA_FOLDER_PATH, "test_mission.yml"),
                adjust_fuel=False,
            ),
            ivc,
        )

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_unlooped_mission_group.csv"),
            use_initializer_iteration=False,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_mission.yml"),
            mission_name="operational",
            adjust_fuel=False,
        ),
        ivc,
    )
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 6589.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:block_fuel"], 15195.0, atol=1.0)


def test_mission_group_breguet_without_loop(cleanup):
    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_unlooped_mission_group.csv"),
            use_initializer_iteration=False,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_breguet.yml"),
            adjust_fuel=False,
        ),
        ivc,
    )
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 6353.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:block_fuel"], 15195.0, atol=1.0)


def test_mission_group_with_loop(cleanup):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    vars = DataFile(input_file_path)
    del vars["data:mission:operational:TOW"]
    ivc = vars.to_ivc()

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_looped_mission_group.csv"),
            use_initializer_iteration=True,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_mission.yml"),
            mission_name="operational",
            add_solver=True,
        ),
        ivc,
    )

    # check loop
    assert_allclose(
        problem["data:mission:operational:TOW"],
        problem["data:mission:operational:OWE"]
        + problem["data:mission:operational:payload"]
        + problem["data:mission:operational:onboard_fuel_at_takeoff"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:mission:operational:needed_onboard_fuel_at_takeoff"],
        problem["data:mission:operational:onboard_fuel_at_takeoff"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:mission:operational:needed_block_fuel"],
        problem["data:mission:operational:needed_onboard_fuel_at_takeoff"]
        + problem["data:mission:operational:taxi_out:fuel"]
        + problem["data:mission:operational:takeoff:fuel"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:mission:operational:needed_block_fuel"], 5682.0, atol=1.0,
    )


def test_mission_group_breguet_with_loop(cleanup):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    vars = DataFile(input_file_path)
    del vars["data:mission:operational:TOW"]
    ivc = vars.to_ivc()

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_looped_mission_group.csv"),
            use_initializer_iteration=True,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_breguet.yml"),
            add_solver=True,
        ),
        ivc,
    )

    # check loop
    assert_allclose(
        problem["data:mission:operational:TOW"],
        problem["data:mission:operational:OWE"]
        + problem["data:mission:operational:payload"]
        + problem["data:mission:operational:onboard_fuel_at_takeoff"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:mission:operational:needed_onboard_fuel_at_takeoff"],
        problem["data:mission:operational:onboard_fuel_at_takeoff"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:mission:operational:needed_block_fuel"],
        problem["data:mission:operational:needed_onboard_fuel_at_takeoff"]
        + problem["data:mission:operational:taxi_out:fuel"]
        + problem["data:mission:operational:takeoff:fuel"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:mission:operational:needed_onboard_fuel_at_takeoff"], 5430.0, atol=1.0,
    )
