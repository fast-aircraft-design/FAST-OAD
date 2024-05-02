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
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fastoad._utils.testing import run_system
from fastoad.io import DataFile
from fastoad.model_base.datacls import MANDATORY_FIELD
from ..mission_run import AdvancedMissionComp
from ..mission_wrapper import MissionWrapper
from ...segments.base import AbstractFlightSegment, RegisterSegment

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


@RegisterSegment("test_segment_A")
@dataclass
class TestSegment(AbstractFlightSegment):
    scalar_parameter: float = MANDATORY_FIELD
    vector_parameter_1: np.ndarray = MANDATORY_FIELD
    vector_parameter_2: np.ndarray = MANDATORY_FIELD
    vector_parameter_3: np.ndarray = MANDATORY_FIELD

    def compute_from(self, start) -> pd.DataFrame:
        return pd.DataFrame([start])

    def compute_from_start_to_target(self, start, target) -> pd.DataFrame:
        pass


def test_with_custom_segment(cleanup, with_dummy_plugin_2):
    input_file_path = DATA_FOLDER_PATH / "test_with_custom_segment.xml"
    ivc = DataFile(input_file_path).to_ivc()

    problem = run_system(
        AdvancedMissionComp(
            propulsion_id="test.wrapper.propulsion.dummy_engine",
            use_initializer_iteration=False,
            mission_file_path=MissionWrapper(
                (DATA_FOLDER_PATH / "test_with_custom_segment.yml").as_posix()
            ),
            mission_name="test",
        ),
        ivc,
    )
