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
from os import makedirs
from shutil import rmtree

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


def test_payload_range(cleanup, with_dummy_plugin_2):

    input_file_path = pth.join(DATA_FOLDER_PATH, "test_payload_range.xml")
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        PayloadRange(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            mission_file_path=pth.join(DATA_FOLDER_PATH, "test_payload_range.yml"),
            mission_name="operational",
            reference_area_variable="data:geometry:aircraft:reference_area",
            nb_contour_points=6,
        ),
        ivc,
    )
    # plot_flight(problem.model.component.flight_points, "test_mission.png")

    # Note: tested value are obtained by asking 1 meter of accuracy for distance routes

    assert_allclose(
        problem["data:payload_range:operational:payload"].squeeze(),
        [19000.0, 19000.0, 15300.0, 10200.0, 5100.0, 0.0],
    )
    assert_allclose(
        problem["data:payload_range:operational:block_fuel"].squeeze(),
        [0.0, 11300.0, 15000.0, 15000.0, 15000.0, 15000.0],
    )
    assert_allclose(
        problem.get_val("data:payload_range:operational:range", "km").squeeze(),
        [0.0, 6745.0, 9594.0, 10454.0, 11378.0, 12377.0],
        atol=0.5,
    )
