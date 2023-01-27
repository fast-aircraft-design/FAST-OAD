#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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
from os import makedirs
from shutil import rmtree

import numpy as np
import pytest
from numpy.testing import assert_allclose

from fastoad._utils.testing import run_system
from fastoad.io import DataFile
from ..payload_range import PayloadRange

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(
    pth.dirname(__file__), "results", pth.splitext(pth.basename(__file__))[0]
)


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    makedirs(RESULTS_FOLDER_PATH)


def test_payload_range_custom_breguet_mission(cleanup, with_dummy_plugin_2):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_payload_range.xml")
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        PayloadRange(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_payload_range.yml"),
            mission_name="operational",
            reference_area_variable="data:geometry:aircraft:reference_area",
            nb_contour_points=6,
            nb_grid_points=10,
            grid_random_seed=0,
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
        [10355.0, 14345.0, 11685.0, 13015.0, 9025.0, 18335.0, 15675.0, 17005.0, 7695.0, 6365.0],
        atol=0.5,
    )
    assert_allclose(
        problem["data:payload_range:operational:grid:block_fuel"],
        [12375.0, 11325.0, 14475.0, 9225.0, 10275.0, 10708.675, 5923.125, 4453.825, 8175.0, 7125.0],
        atol=0.5,
    )
    assert_allclose(
        problem.get_val("data:payload_range:operational:grid:range", "km").squeeze(),
        [8581.6, 7319.8, 9841.1, 6016.4, 7225.8, 6445.2, 3464.0, 2356.6, 5782.2, 5090.5],
        atol=0.5,
    )
    assert_allclose(
        problem["data:payload_range:operational:grid:duration"].squeeze(),
        [32949.6, 27518.6, 38370.6, 21909.1, 27114.4, 23754.4, 10923.6, 6157.4, 20901.1, 17923.8],
        atol=0.5,
    )


def test_payload_range_sizing_breguet(cleanup, with_dummy_plugin_2):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_payload_range.xml")
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

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_payload_range.xml")
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
        problem["data:payload_range:sizing:grid:payload"], np.array([12897.0, 16838.0]), atol=0.5
    )
    assert_allclose(
        problem["data:payload_range:sizing:grid:block_fuel"], np.array([8470.0, 11858.0]), atol=0.5
    )
    assert_allclose(
        problem.get_val("data:payload_range:sizing:grid:range", "km").squeeze(),
        [4488.0, 6256.0],
        atol=0.5,
    )
    assert_allclose(
        problem.get_val("data:payload_range:sizing:grid:duration", "min").squeeze(),
        [330.0, 458.0],
        atol=0.5,
    )
