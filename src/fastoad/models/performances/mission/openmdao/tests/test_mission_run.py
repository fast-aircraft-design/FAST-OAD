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
from scipy.constants import nautical_mile

from fastoad._utils.testing import run_system
from fastoad.io import DataFile
from ..mission_run import MissionComp

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_mission_run(cleanup, with_dummy_plugin_2):

    input_file_path = DATA_FOLDER_PATH / "test_mission_run.xml"
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        MissionComp(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            out_file=(RESULTS_FOLDER_PATH / "mission.csv").as_posix(),
            mission_file_path=(DATA_FOLDER_PATH / "test_mission.yml").as_posix(),
            mission_name="operational",
            reference_area_variable="data:geometry:aircraft:reference_area",
            variable_prefix="data:payload_range",
        ),
        ivc,
    )
    # plot_flight(problem.model.component.flight_points, "test_mission.png")

    # Note: tested value are obtained by asking 1 meter of accuracy for distance routes

    assert_allclose(
        problem["data:payload_range:operational:main_route:initial_climb:duration"], 34.0, atol=1.0
    )
    assert_allclose(
        problem["data:payload_range:operational:main_route:initial_climb:fuel"], 121.0, atol=1.0
    )
    assert_allclose(
        problem["data:payload_range:operational:main_route:initial_climb:distance"],
        3600.0,
        atol=1.0,
    )

    assert_allclose(
        problem["data:payload_range:operational:main_route:climb:duration"], 236.0, atol=1.0
    )
    assert_allclose(
        problem["data:payload_range:operational:main_route:climb:fuel"], 727.0, atol=1.0
    )
    assert_allclose(
        problem["data:payload_range:operational:main_route:climb:distance"], 43065.0, atol=1.0
    )

    assert_allclose(
        problem["data:payload_range:operational:main_route:cruise:duration"], 14736.0, atol=10.0
    )
    assert_allclose(
        problem["data:payload_range:operational:main_route:cruise:fuel"], 5167.0, atol=1.0
    )
    assert_allclose(
        problem["data:payload_range:operational:main_route:cruise:distance"], 3392590.0, atol=500.0
    )

    assert_allclose(
        problem["data:payload_range:operational:main_route:descent:duration"], 1424.0, atol=10.0
    )
    assert_allclose(
        problem["data:payload_range:operational:main_route:descent:fuel"], 192.0, atol=1.0
    )
    assert_allclose(
        problem["data:payload_range:operational:main_route:descent:distance"], 264451.0, atol=500.0
    )

    assert_allclose(problem["data:payload_range:operational:needed_block_fuel"], 6590.0, atol=1.0)
    assert_allclose(
        problem["data:payload_range:operational:distance"], 2000.0 * nautical_mile, atol=500.0
    )
    assert_allclose(problem["data:payload_range:operational:duration"], 16573.0, atol=10.0)
