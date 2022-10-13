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


import os.path as pth
from shutil import rmtree

import pytest
from numpy.testing import assert_allclose
from scipy.constants import foot, knot, nautical_mile

from fastoad._utils.testing import run_system
from fastoad.io import DataFile
from ..mission import Mission
from ..mission_component import MissionComponent
from ..mission_wrapper import MissionWrapper
from ...mission_definition.exceptions import FastMissionFileMissingMissionNameError

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


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

    problem = run_system(
        MissionComponent(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "mission.csv"),
            use_initializer_iteration=False,
            mission_wrapper=MissionWrapper(pth.join(DATA_FOLDER_PATH, "test_mission.yml")),
            mission_name="operational",
            reference_area_variable="data:geometry:aircraft:reference_area",
        ),
        ivc,
    )
    # plot_flight(problem.model.component.flight_points, "test_mission.png")

    # Note: tested value are obtained by asking 1 meter of accuracy for distance routes

    assert_allclose(
        problem["data:mission:operational:main_route:initial_climb:duration"], 34.0, atol=1.0
    )
    assert_allclose(
        problem["data:mission:operational:main_route:initial_climb:fuel"], 121.0, atol=1.0
    )
    assert_allclose(
        problem["data:mission:operational:main_route:initial_climb:distance"], 3600.0, atol=1.0
    )

    assert_allclose(problem["data:mission:operational:main_route:climb:duration"], 236.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:main_route:climb:fuel"], 727.0, atol=1.0)
    assert_allclose(
        problem["data:mission:operational:main_route:climb:distance"], 43065.0, atol=1.0
    )

    assert_allclose(
        problem["data:mission:operational:main_route:cruise:duration"], 14736.0, atol=10.0
    )
    assert_allclose(problem["data:mission:operational:main_route:cruise:fuel"], 5167.0, atol=1.0)
    assert_allclose(
        problem["data:mission:operational:main_route:cruise:distance"], 3392590.0, atol=500.0
    )

    assert_allclose(
        problem["data:mission:operational:main_route:descent:duration"], 1424.0, atol=10.0
    )
    assert_allclose(problem["data:mission:operational:main_route:descent:fuel"], 192.0, atol=1.0)
    assert_allclose(
        problem["data:mission:operational:main_route:descent:distance"], 264451.0, atol=500.0
    )

    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 6590.0, atol=1.0)
    assert_allclose(
        problem["data:mission:operational:distance"], 2000.0 * nautical_mile, atol=500.0
    )
    assert_allclose(problem["data:mission:operational:duration"], 16573.0, atol=10.0)


def test_mission_component_breguet(cleanup, with_dummy_plugin_2):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    vars = DataFile(input_file_path)
    ivc = vars.to_ivc()
    ivc.add_output("data:mission:operational:ramp_weight", 70100.0, units="kg")

    problem = run_system(
        MissionComponent(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "breguet.csv"),
            use_initializer_iteration=False,
            mission_wrapper=MissionWrapper(
                pth.join(DATA_FOLDER_PATH, "test_breguet_from_block_fuel.yml")
            ),
            mission_name="operational",
            reference_area_variable="data:geometry:aircraft:reference_area",
        ),
        ivc,
    )
    # plot_flight(problem.model.component.flight_points, "test_mission_component_breguet.png")
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 6256.0, atol=1.0)

    assert_allclose(problem["data:mission:operational:taxi_out:fuel"], 100.0, atol=1.0)

    assert_allclose(problem["data:mission:operational:main_route:climb:duration"], 0.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:main_route:climb:fuel"], 839.0, atol=1.0)
    assert_allclose(
        problem["data:mission:operational:main_route:climb:distance"], 463000.0, atol=1.0
    )

    assert_allclose(
        problem["data:mission:operational:main_route:cruise:duration"], 11695.0, atol=1.0
    )
    assert_allclose(problem["data:mission:operational:main_route:cruise:fuel"], 4197.0, atol=1.0)
    assert_allclose(
        problem["data:mission:operational:main_route:cruise:distance"], 2778000.0, atol=1.0
    )

    assert_allclose(problem["data:mission:operational:main_route:descent:duration"], 0.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:main_route:descent:fuel"], 1025.0, atol=1.0)
    assert_allclose(
        problem["data:mission:operational:main_route:descent:distance"], 463000.0, atol=1.0
    )


def test_mission_group_without_fuel_adjustment(cleanup, with_dummy_plugin_2):
    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    ivc = DataFile(input_file_path).to_ivc()

    with pytest.raises(FastMissionFileMissingMissionNameError):
        run_system(
            Mission(
                propulsion_id="test.wrapper.propulsion.dummy_engine",
                out_file=pth.join(RESULTS_FOLDER_PATH, "unlooped_mission_group.csv"),
                use_initializer_iteration=False,
                mission_file_path=pth.join(DATA_FOLDER_PATH, "test_mission.yml"),
                adjust_fuel=False,
                reference_area_variable="data:geometry:aircraft:reference_area",
                add_solver=True,
            ),
            ivc,
        )

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "unlooped_mission_group.csv"),
            use_initializer_iteration=False,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_mission.yml"),
            mission_name="operational",
            adjust_fuel=False,
            reference_area_variable="data:geometry:aircraft:reference_area",
            add_solver=True,
        ),
        ivc,
    )
    assert_allclose(
        problem["data:mission:operational:consumed_fuel_before_input_weight"], 195.4, atol=0.1
    )
    assert_allclose(problem["data:mission:operational:ZFW"], 55000.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 6590.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:block_fuel"], 15195.0, atol=1.0)


def test_mission_group_breguet_without_fuel_adjustment(cleanup, with_dummy_plugin_2):
    input_file_path = pth.join(DATA_FOLDER_PATH, "test_breguet.xml")
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "unlooped_breguet_mission_group.csv"),
            use_initializer_iteration=False,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_breguet.yml"),
            adjust_fuel=False,
            reference_area_variable="data:geometry:aircraft:reference_area",
        ),
        ivc,
    )
    assert_allclose(problem["data:mission:operational:consumed_fuel_before_input_weight"], 0.0)
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 6245.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:ZFW"], 55000.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:block_fuel"], 15000.0, atol=1.0)


def test_mission_group_with_fuel_adjustment(cleanup, with_dummy_plugin_2):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_mission.xml")
    vars = DataFile(input_file_path)
    del vars["data:mission:operational:TOW"]
    ivc = vars.to_ivc()

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "looped_mission_group.csv"),
            use_initializer_iteration=True,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_mission.yml"),
            mission_name="operational",
            add_solver=True,
            reference_area_variable="data:geometry:aircraft:reference_area",
        ),
        ivc,
    )

    # check loop
    assert_allclose(
        problem["data:mission:operational:ZFW"],
        problem["data:mission:operational:OWE"] + problem["data:mission:operational:payload"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:mission:operational:block_fuel"] + problem["data:mission:operational:ZFW"],
        problem["data:mission:operational:TOW"]
        + problem["data:mission:operational:consumed_fuel_before_input_weight"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:mission:operational:needed_block_fuel"],
        problem["data:mission:operational:block_fuel"],
        atol=1.0,
    )

    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 5682.0, atol=1.0)


def test_mission_group_breguet_with_fuel_adjustment(cleanup, with_dummy_plugin_2):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_breguet.xml")
    vars = DataFile(input_file_path)
    del vars["data:mission:operational:ramp_weight"]
    ivc = vars.to_ivc()

    problem = run_system(
        Mission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=pth.join(RESULTS_FOLDER_PATH, "looped_breguet_mission_group.csv"),
            use_initializer_iteration=True,
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_breguet.yml"),
            add_solver=True,
            reference_area_variable="data:geometry:aircraft:reference_area",
        ),
        ivc,
    )

    # check loop
    assert_allclose(
        problem["data:mission:operational:ZFW"],
        problem["data:mission:operational:OWE"] + problem["data:mission:operational:payload"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:mission:operational:block_fuel"] + problem["data:mission:operational:ZFW"],
        problem["data:mission:operational:ramp_weight"]
        + problem["data:mission:operational:consumed_fuel_before_input_weight"],
        atol=1.0,
    )
    assert_allclose(problem["data:mission:operational:consumed_fuel_before_input_weight"], 0.0)
    assert_allclose(
        problem["data:mission:operational:needed_block_fuel"],
        problem["data:mission:operational:block_fuel"],
        atol=1.0,
    )
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 5525.0, atol=1.0)
