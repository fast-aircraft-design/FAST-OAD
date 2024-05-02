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

import numpy as np
import pytest
from numpy.testing import assert_allclose

from fastoad._utils.testing import run_system
from fastoad.io import DataFile
from ..payload_range import PayloadRange

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_payload_range_custom_breguet_mission(cleanup, with_dummy_plugin_2):

    input_file_path = DATA_FOLDER_PATH / "test_payload_range.xml"
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        PayloadRange(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            mission_file_path=(DATA_FOLDER_PATH / "test_payload_range.yml").as_posix(),
            mission_name="operational",
            reference_area_variable="data:geometry:aircraft:reference_area",
            nb_contour_points=6,
            nb_grid_points=8,
            grid_random_seed=0,
            grid_lhs_criterion="center",
        ),
        ivc,
    )

    assert_allclose(
        problem["data:payload_range:operational:payload"],
        [19000.0, 19000.0, 15300.0, 10200.0, 5100.0, 0.0],
    )
    assert_allclose(
        problem["data:payload_range:operational:block_fuel"],
        [0.0, 11300.0, 15000.0, 15000.0, 15000.0, 15000.0],
    )
    assert_allclose(
        problem.get_val("data:payload_range:operational:range", "km").squeeze(),
        [0.0, 6745.0, 9594.0, 10454.0, 11378.0, 12377.0],
        atol=0.5,
    )

    assert_allclose(
        problem["data:payload_range:operational:grid:payload"],
        [13181.0, 8194.0, 6531.25, 9856.0, 16506.0, 18169.0, 14844.0, 11519.0, 19000.0, 15300.0],
        atol=0.5,
    )
    assert_allclose(
        problem["data:payload_range:operational:grid:block_fuel"],
        [11719.0, 6469.0, 10406.0, 7781.0, 11983.0, 11601.0, 5156.0, 9094.0, 11300.0, 15000.0],
        atol=0.5,
    )
    assert_allclose(
        problem.get_val("data:payload_range:operational:grid:range", "km").squeeze(),
        [7736.0, 4422.0, 7634.0, 5275.0, 7485.0, 7033.0, 2976.0, 6078.0, 6745.0, 9594.0],
        atol=0.5,
    )
    assert_allclose(
        problem["data:payload_range:operational:grid:duration"].squeeze(),
        [29311.0, 15048.0, 28873.0, 18719.0, 28229.0, 26286.0, 8821.0, 22175.0, 25046.0, 37307.0],
        atol=0.5,
    )
    assert_allclose(
        problem["data:payload_range:operational:grid:specific_burned_fuel"].squeeze(),
        [
            2.1283e-4,
            3.3062e-4,
            3.8651e-4,
            2.7715e-4,
            1.7963e-4,
            1.6813e-4,
            2.1620e-4,
            2.4055e-4,
            1.6329e-4,
            1.8925e-4,
        ],
        rtol=1.0e-4,
    )


def test_payload_range_sizing_breguet(cleanup, with_dummy_plugin_2):

    input_file_path = DATA_FOLDER_PATH / "test_payload_range.xml"
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        PayloadRange(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            mission_file_path="::sizing_breguet",
            mission_name="sizing",
            reference_area_variable="data:geometry:aircraft:reference_area",
            nb_contour_points=7,
            variable_prefix="data:PR_diagram",
        ),
        ivc,
    )
    assert_allclose(
        problem["data:PR_diagram:sizing:payload"],
        [19000.0, 19000.0, 15300.0, 11475.0, 7650.0, 3825.0, 0.0],
    )
    assert_allclose(
        problem["data:PR_diagram:sizing:block_fuel"],
        [0.0, 11300.0, 15000.0, 15000.0, 15000.0, 15000.0, 15000.0],
    )
    assert_allclose(
        problem.get_val("data:PR_diagram:sizing:range", "km").squeeze(),
        [0.0, 3313.0, 6173.0, 6912.0, 7763.0, 8750.0, 9908.0],
        atol=0.5,
    )

    for var_name in ["payload", "block_fuel", "range", "duration"]:
        with pytest.raises(KeyError):
            problem[f"data:PR_diagram:sizing:grid:{var_name}"]


def test_payload_range_sizing_mission(cleanup, with_dummy_plugin_2):

    input_file_path = DATA_FOLDER_PATH / "test_payload_range.xml"
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        PayloadRange(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            mission_file_path="::sizing_mission",
            mission_name="sizing",
            reference_area_variable="data:geometry:aircraft:reference_area",
            nb_contour_points=4,
            nb_grid_points=2,
            grid_random_seed=0,
            grid_lhs_criterion=None,
            min_payload_ratio=0.5,
            min_block_fuel_ratio=0.4,
        ),
        ivc,
    )
    assert_allclose(problem["data:payload_range:sizing:payload"], [19000.0, 19000.0, 15300.0, 0.0])
    assert_allclose(
        problem["data:payload_range:sizing:block_fuel"], [0.0, 11300.0, 15000.0, 15000.0]
    )
    assert_allclose(
        problem.get_val("data:payload_range:sizing:range", "km").squeeze(),
        [0.0, 5649.0, 8298.0, 11559.0],
        atol=0.5,
    )

    assert_allclose(
        problem["data:payload_range:sizing:grid:payload"],
        np.array([12897.0, 16838.0, 19000.0, 15300.0]),
        atol=0.5,
    )
    assert_allclose(
        problem["data:payload_range:sizing:grid:block_fuel"],
        np.array([8470.0, 11858.0, 11300.0, 15000.0]),
        atol=0.5,
    )
    assert_allclose(
        problem.get_val("data:payload_range:sizing:grid:range", "km").squeeze(),
        [4488.0, 6256.0, 5649.0, 8298.0],
        atol=0.5,
    )
    assert_allclose(
        problem.get_val("data:payload_range:sizing:grid:duration", "min").squeeze(),
        [330.0, 458.0, 414.0, 605.0],
        atol=0.5,
    )
    assert_allclose(
        problem.get_val("data:payload_range:sizing:grid:specific_burned_fuel", "km**-1").squeeze(),
        [1.463138e-4, 1.12571e-4, 1.05282e-4, 1.18153e-4],
        rtol=1.0e-4,
    )
