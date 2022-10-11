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
from dataclasses import dataclass
from shutil import rmtree

import numpy as np
import pandas as pd
import pytest

from fastoad._utils.testing import run_system
from fastoad.io import DataFile
from fastoad.model_base.datacls import MANDATORY_FIELD
from ..mission_component import MissionComponent
from ..mission_wrapper import MissionWrapper
from ...segments.base import AbstractFlightSegment

# noinspection PyUnresolvedReferences
from ...segments.start import Start

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


@dataclass
class TestSegment(AbstractFlightSegment, mission_file_keyword="test_segment_A"):
    scalar_parameter: float = MANDATORY_FIELD
    vector_parameter_1: np.ndarray = MANDATORY_FIELD
    vector_parameter_2: np.ndarray = MANDATORY_FIELD
    vector_parameter_3: np.ndarray = MANDATORY_FIELD

    def compute_from(self, start) -> pd.DataFrame:
        return pd.DataFrame([start])

    def compute_from_start_to_target(self, start, target) -> pd.DataFrame:
        pass


TestSegment._attribute_units["vector_parameter_1"] = "kg"
TestSegment._attribute_units["vector_parameter_3"] = "m"


def test_with_custom_segment(cleanup, with_dummy_plugin_2):
    input_file_path = pth.join(DATA_FOLDER_PATH, "test_with_custom_segment.xml")
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        MissionComponent(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            use_initializer_iteration=False,
            mission_wrapper=MissionWrapper(
                pth.join(DATA_FOLDER_PATH, "test_with_custom_segment.yml")
            ),
            mission_name="test",
        ),
        ivc,
    )
