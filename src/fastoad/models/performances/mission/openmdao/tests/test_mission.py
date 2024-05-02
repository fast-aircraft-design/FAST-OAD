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
from scipy.constants import foot, knot, nautical_mile

from fastoad._utils.testing import run_system
from fastoad.io import DataFile, VariableIO
from ..mission import OMMission
from ..mission_run import AdvancedMissionComp
from ..mission_wrapper import MissionWrapper
from ...mission_definition.exceptions import FastMissionFileMissingMissionNameError

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


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

    plt.savefig(RESULTS_FOLDER_PATH / fig_filename)
    plt.close()


def test_mission_component(cleanup, with_dummy_plugin_2):
    # Also checking behavior when is_sizing is True

    input_file_path = DATA_FOLDER_PATH / "test_mission.xml"
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        AdvancedMissionComp(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "mission.csv").as_posix(),
            use_initializer_iteration=False,
            mission_file_path=MissionWrapper(
                (DATA_FOLDER_PATH / "test_mission.yml").as_posix(),
                mission_name="operational",
            ),
            reference_area_variable="data:geometry:aircraft:reference_area",
            is_sizing=True,
        ),
        ivc,
    )
    # plot_flight(problem.model.component.flight_points, "test_mission.png")

    # Note: tested value are obtained by asking 1 meter of accuracy for distance routes
    assert_allclose(problem["data:mission:operational:taxi_out:fuel"], 100.0, atol=1.0)
    assert_allclose(problem["data:mission:operational:takeoff:fuel"], 95.0, atol=1.0)
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

    # Outputs when is_sizing is True
    assert_allclose(problem["data:weight:aircraft:sizing_block_fuel"], 6590.0, atol=1.0)
    assert_allclose(
        problem["data:weight:aircraft:sizing_onboard_fuel_at_input_weight"], 6395.0, atol=1.0
    )


def test_mission_component_breguet(cleanup, with_dummy_plugin_2):

    input_file_path = DATA_FOLDER_PATH / "test_mission.xml"
    vars = DataFile(input_file_path)
    ivc = vars.to_ivc()
    ivc.add_output("data:mission:operational:ramp_weight", 70100.0, units="kg")

    problem = run_system(
        AdvancedMissionComp(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "breguet.csv").as_posix(),
            use_initializer_iteration=False,
            mission_file_path=MissionWrapper(
                (DATA_FOLDER_PATH / "test_breguet_from_block_fuel.yml").as_posix(),
                mission_name="operational",
            ),
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
    input_file_path = DATA_FOLDER_PATH / "test_mission.xml"
    ivc = DataFile(input_file_path).to_ivc()

    with pytest.raises(FastMissionFileMissingMissionNameError):
        run_system(
            OMMission(
                propulsion_id="test.wrapper.propulsion.dummy_engine",
                out_file=(RESULTS_FOLDER_PATH / "unlooped_mission_group.csv").as_posix(),
                use_initializer_iteration=False,
                mission_file_path=(DATA_FOLDER_PATH / "test_mission.yml").as_posix(),
                adjust_fuel=False,
                reference_area_variable="data:geometry:aircraft:reference_area",
                add_solver=True,
            ),
            ivc,
        )

    problem = run_system(
        OMMission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "unlooped_mission_group.csv").as_posix(),
            use_initializer_iteration=False,
            mission_file_path=(DATA_FOLDER_PATH / "test_mission.yml").as_posix(),
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
    input_file_path = DATA_FOLDER_PATH / "test_breguet.xml"
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        OMMission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "unlooped_breguet_mission_group.csv").as_posix(),
            use_initializer_iteration=False,
            mission_file_path=(DATA_FOLDER_PATH / "test_breguet.yml").as_posix(),
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

    input_file_path = DATA_FOLDER_PATH / "test_mission.xml"
    vars = DataFile(input_file_path)
    del vars["data:mission:operational:TOW"]
    ivc = vars.to_ivc()

    problem = run_system(
        OMMission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "looped_mission_group.csv").as_posix(),
            use_initializer_iteration=True,
            mission_file_path=(DATA_FOLDER_PATH / "test_mission.yml").as_posix(),
            mission_name="operational",
            add_solver=True,
            reference_area_variable="data:geometry:aircraft:reference_area",
        ),
        ivc,
    )

    # check loop
    assert_allclose(
        problem["data:mission:operational:ZFW"],
        problem["data:weight:aircraft:OWE"] + problem["data:mission:operational:payload"],
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
    assert_allclose(
        problem.get_val("data:mission:operational:specific_burned_fuel", "km**-1"),
        1.02283e-4,
        rtol=1.0e-5,
    )


def test_mission_group_breguet_with_fuel_adjustment(cleanup, with_dummy_plugin_2):
    # Also checking behavior when is_sizing is True

    input_file_path = DATA_FOLDER_PATH / "test_breguet.xml"
    vars = DataFile(input_file_path)
    del vars["data:mission:operational:ramp_weight"]
    ivc = vars.to_ivc()

    problem = run_system(
        OMMission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "looped_breguet_mission_group.csv").as_posix(),
            use_initializer_iteration=True,
            mission_file_path=(DATA_FOLDER_PATH / "test_breguet.yml").as_posix(),
            add_solver=True,
            reference_area_variable="data:geometry:aircraft:reference_area",
            is_sizing=True,
        ),
        ivc,
    )

    # check loop
    assert_allclose(
        problem["data:mission:operational:ZFW"],
        problem["data:weight:aircraft:OWE"] + problem["data:weight:aircraft:payload"],
        atol=1.0,
    )
    assert_allclose(
        problem["data:weight:aircraft:sizing_block_fuel"] + problem["data:mission:operational:ZFW"],
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
    assert_allclose(
        problem["data:mission:operational:needed_block_fuel"],
        problem["data:weight:aircraft:sizing_block_fuel"],
        atol=1.0,
    )
    assert_allclose(problem["data:mission:operational:needed_block_fuel"], 5449.0, atol=1.0)


def test_mission_group_with_fuel_objective(cleanup, with_dummy_plugin_2):

    input_file_path = DATA_FOLDER_PATH / "test_mission.xml"
    vars = DataFile(input_file_path)
    ivc = vars.to_ivc()

    problem = run_system(
        OMMission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "fuel_as_objective.csv").as_posix(),
            use_initializer_iteration=False,
            mission_file_path=(DATA_FOLDER_PATH / "test_mission.yml").as_posix(),
            mission_name="fuel_as_objective",
            add_solver=True,
            adjust_fuel=False,
            compute_input_weight=True,
            reference_area_variable="data:geometry:aircraft:reference_area",
        ),
        ivc,
    )

    # check loop
    assert_allclose(
        problem["data:mission:fuel_as_objective:ZFW"],
        problem["data:mission:fuel_as_objective:OWE"]
        + problem["data:mission:fuel_as_objective:payload"],
        atol=1.0,
    )

    assert_allclose(
        problem["data:mission:fuel_as_objective:needed_block_fuel"],
        problem["data:mission:fuel_as_objective:block_fuel"],
        atol=1.0,
    )

    assert_allclose(problem["data:mission:fuel_as_objective:needed_block_fuel"], 10000.0, atol=1.0)
    assert_allclose(problem["data:mission:fuel_as_objective:reserve:fuel"], 260.0, atol=1.0)


def test_mission_group_with_CL_limitation(cleanup, with_dummy_plugin_2):

    input_file_path = DATA_FOLDER_PATH / "test_mission.xml"
    vars = VariableIO(input_file_path.as_posix()).read(ignore=["data:mission:operational:max_CL"])
    ivc = vars.to_ivc()

    # Activate CL limitation during cruise and climb
    ivc.add_output("data:mission:operational:max_CL", val=0.45)

    problem = run_system(
        AdvancedMissionComp(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "CL_limitation_1.csv").as_posix(),
            use_initializer_iteration=False,
            mission_file_path=MissionWrapper(
                (DATA_FOLDER_PATH / "test_mission.yml").as_posix(),
                mission_name="operational",
            ),
            reference_area_variable="data:geometry:aircraft:reference_area",
        ),
        ivc,
    )

    flight_points = problem.model.component.flight_points
    climb_points = flight_points.loc[flight_points["name"] == "operational:main_route:climb"]
    CL_end_climb = climb_points.CL.iloc[-1]
    altitude_end_climb = climb_points.altitude.iloc[-1]

    # check CL and flight level, CL is lower than 0.45 because the climb phase stops at the closest flight level.
    assert_allclose(CL_end_climb, 0.445, atol=1e-3)
    assert_allclose(altitude_end_climb, 9753.6, atol=1e-1)

    # Now check climbing cruise with contant CL
    ivc.add_output("data:mission:operational_optimal:max_CL", val=0.45)
    ivc.add_output("data:mission:operational_optimal:taxi_out:thrust_rate", val=0.3)
    ivc.add_output("data:mission:operational_optimal:taxi_out:duration", val=300, units="s")
    ivc.add_output("data:mission:operational_optimal:takeoff:fuel", val=100, units="kg")
    ivc.add_output("data:mission:operational_optimal:takeoff:V2", val=70, units="m/s")
    ivc.add_output("data:mission:operational_optimal:TOW", val=70000, units="kg")

    problem = run_system(
        AdvancedMissionComp(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "CL_limitation_2.csv").as_posix(),
            use_initializer_iteration=False,
            mission_file_path=MissionWrapper(
                (DATA_FOLDER_PATH / "test_mission.yml").as_posix(),
                mission_name="operational_optimal",
            ),
            reference_area_variable="data:geometry:aircraft:reference_area",
        ),
        ivc,
    )

    flight_points = problem.model.component.flight_points
    climb_points = flight_points.loc[
        flight_points["name"] == "operational_optimal:main_route_optimal:climb_optimal"
    ]
    cruise_points = flight_points.loc[
        flight_points["name"] == "operational_optimal:main_route_optimal:cruise"
    ]
    CL_end_climb = climb_points.CL.iloc[-1]
    altitude_end_climb = climb_points.altitude.iloc[-1]
    altitude_end_cruise = cruise_points.altitude.iloc[-1]
    CL_end_cruise = cruise_points.CL.iloc[-1]

    # Check CL and altitude for a climbing cruise at constant CL.
    assert_allclose(CL_end_climb, 0.45, atol=1e-3)
    assert_allclose(CL_end_cruise, 0.45, atol=1e-3)
    assert_allclose(altitude_end_climb, 9821.85, atol=1e-1)
    assert_allclose(altitude_end_cruise, 10343.68, atol=1e-1)


def test_mission_group_without_route(cleanup, with_dummy_plugin_2):
    input_file_path = DATA_FOLDER_PATH / "test_mission.xml"
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        OMMission(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "without_route_mission_group.csv").as_posix(),
            use_initializer_iteration=False,
            mission_file_path=(DATA_FOLDER_PATH / "test_mission.yml").as_posix(),
            mission_name="without_route",
            adjust_fuel=True,
            reference_area_variable="data:geometry:aircraft:reference_area",
            add_solver=True,
        ),
        ivc,
    )
    assert_allclose(
        problem["data:mission:without_route:consumed_fuel_before_input_weight"], 195.4, atol=0.1
    )
    assert_allclose(problem["data:mission:without_route:ZFW"], 55000.0, atol=1.0)
    assert_allclose(problem["data:mission:without_route:needed_block_fuel"], 1136.8, atol=1.0)
    assert_allclose(problem["data:mission:without_route:block_fuel"], 1136.8, atol=1.0)
