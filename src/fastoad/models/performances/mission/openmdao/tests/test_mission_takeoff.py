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

import pytest
from numpy.testing import assert_allclose
from scipy.constants import foot, knot

from fastoad._utils.testing import run_system
from fastoad.io import DataFile
from ..mission import Mission, MissionComponent
from ..mission_wrapper import MissionWrapper
from ...mission_definition.exceptions import FastMissionFileMissingMissionNameError

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")

# Using the decorator directly on the class would prevent it from being available
# in this file.
# RegisterPropulsion("test.wrapper.propulsion.dummy_engine")(DummyEngineWrapper)

# End of propulsion definition -------------------------------------------------


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    mkdir(RESULTS_FOLDER_PATH)


def plot_flight(flight_points, fig_filename):
    from matplotlib import pyplot as plt
    from matplotlib.ticker import MultipleLocator

    plt.figure(figsize=(12, 12))
    ax1 = plt.subplot(2, 1, 1)
    plt.plot(
        flight_points["ground_distance [m]"] / 1000.0, flight_points["altitude [m]"] / foot, "o-"
    )
    plt.xlabel("distance [km]")
    plt.ylabel("altitude [ft]")
    ax1.xaxis.set_minor_locator(MultipleLocator(50))
    ax1.yaxis.set_minor_locator(MultipleLocator(500))
    plt.grid(which="major", color="k")
    plt.grid(which="minor")

    ax2 = plt.subplot(2, 1, 2)
    lines = []
    lines += plt.plot(
        flight_points["ground_distance [m]"] / 1000.0,
        flight_points["true_airspeed [m/s]"],
        "b-",
        label="TAS [m/s]",
    )
    lines += plt.plot(
        flight_points["ground_distance [m]"] / 1000.0,
        flight_points["equivalent_airspeed [m/s]"] / knot,
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
        flight_points["ground_distance [m]"] / 1000.0,
        flight_points["mach [-]"],
        "r.-",
        label="Mach",
    )
    plt.ylabel("Mach")

    labels = [l.get_label() for l in lines]
    plt.legend(lines, labels, loc=0)

    plt.savefig(pth.join(RESULTS_FOLDER_PATH, fig_filename))
    plt.close()


def test_mission_component(cleanup, with_dummy_plugin_2):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    ivc = DataFile(input_file_path).to_ivc()

    ivc.add_output("data:geometry:wing:area", 130.0, units="m**2")
    ivc.add_output("data:mission:operational_wo_gnd_effect:TOW", 70000, units="kg")
    ivc.add_output("data:mission:operational_wo_gnd_effect:OWE", 40000, units="kg")
    ivc.add_output("data:mission:operational_wo_gnd_effect:ramp_weight", 70200, units="kg")

    problem = run_system(
        MissionComponent(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_mission.csv"),
            use_initializer_iteration=False,
            mission_wrapper=MissionWrapper(pth.join(DATA_FOLDER_PATH, "test_mission_takeoff.yml")),
            mission_name="operational_wo_gnd_effect",
        ),
        ivc,
    )
    # plot_flight(problem.model.component.flight_points, "test_mission.png")
    take_off_distance = problem[
        "data:mission:operational_wo_gnd_effect:takeoff_wo_gnd_effect:distance"
    ]
    assert_allclose(take_off_distance, 1774, atol=1.0)
    assert_allclose(
        problem["data:mission:operational_wo_gnd_effect:needed_block_fuel"], 6503, atol=1.0
    )
    assert_allclose(
        problem["data:mission:operational_wo_gnd_effect:takeoff_wo_gnd_effect:fuel"],
        122.7,
        atol=1e-1,
    )
    assert_allclose(
        problem["data:mission:operational_wo_gnd_effect:takeoff_wo_gnd_effect:duration"],
        34.1,
        atol=1e-1,
    )


def test_ground_effect(cleanup, with_dummy_plugin_2):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    datafile = DataFile(input_file_path)
    del datafile["data:mission:operational:takeoff:fuel"]

    ivc = datafile.to_ivc()
    ivc.add_output("data:geometry:wing:area", 130.33, units="m**2")
    ivc.add_output("data:mission:operational:ramp_weight", 70200, units="kg")

    problem = run_system(
        MissionComponent(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_mission_to.csv"),
            use_initializer_iteration=False,
            mission_wrapper=MissionWrapper(pth.join(DATA_FOLDER_PATH, "test_mission_takeoff.yml")),
            mission_name="operational",
        ),
        ivc,
    )
    plot_flight(problem.model.component.flight_points, "test_mission.png")
    take_off_distance = problem["data:mission:operational:takeoff:distance"]
    assert_allclose(take_off_distance, 1768, atol=1.0)
    assert_allclose(problem["data:mission:operational:takeoff:fuel"], 122.4, atol=1e-1)
    assert_allclose(problem["data:mission:operational:takeoff:duration"], 34.0, atol=1e-1)


def test_start_stop(cleanup, with_dummy_plugin_2):
    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    ivc = DataFile(input_file_path).to_ivc()

    ivc.add_output("data:geometry:wing:area", 130.0, units="m**2")
    ivc.add_output("data:mission:start_stop_mission:TOW", 79000, units="kg")
    ivc.add_output("data:mission:start_stop_mission:OWE", 40000, units="kg")
    ivc.add_output("data:mission:start_stop_mission:ramp_weight", 70200, units="kg")

    problem = run_system(
        MissionComponent(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_mission_start_stop.csv"),
            use_initializer_iteration=False,
            mission_wrapper=MissionWrapper(pth.join(DATA_FOLDER_PATH, "test_mission_takeoff.yml")),
            mission_name="start_stop_mission",
        ),
        ivc,
    )
    plot_flight(problem.model.component.flight_points, "test_mission.png")
    start_stop_distance = problem["data:mission:start_stop_mission:start_stop:distance"]
    assert_allclose(start_stop_distance, 1659, atol=1.0)
    assert_allclose(problem["data:mission:start_stop_mission:start_stop:duration"], 42.8, atol=1e-1)


def test_mission_group_without_loop(cleanup, with_dummy_plugin_2):
    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    datafile = DataFile(input_file_path)
    del datafile["data:mission:operational:takeoff:fuel"]
    ivc = datafile.to_ivc()

    ivc.add_output("data:geometry:wing:area", 100.0, units="m**2")

    with pytest.raises(FastMissionFileMissingMissionNameError):
        run_system(
            Mission(
                propulsion_id="test.wrapper.propulsion.dummy_engine",
                out_file=pth.join(RESULTS_FOLDER_PATH, "test_unlooped_mission_group.csv"),
                use_initializer_iteration=False,
                mission_file_path=pth.join(DATA_FOLDER_PATH, "test_mission_takeoff.yml"),
                adjust_fuel=False,
            ),
            ivc,
        )

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_unlooped_mission_group.csv"),
            use_initializer_iteration=False,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_mission_takeoff.yml"),
            mission_name="operational",
            adjust_fuel=False,
        ),
        ivc,
    )
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 6302, atol=1.0)
    assert_allclose(problem["data:mission:operational:block_fuel"], 15000.0, atol=1.0)


def test_mission_group_with_loop(cleanup, with_dummy_plugin_2):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    vars = DataFile(input_file_path)
    del vars["data:mission:operational:TOW"]
    del vars["data:mission:operational:takeoff:fuel"]
    ivc = vars.to_ivc()

    ivc.add_output("data:geometry:wing:area", 100.0, units="m**2")

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "test_looped_mission_group.csv"),
            use_initializer_iteration=True,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_mission_takeoff.yml"),
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
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 5464, atol=1.0)
