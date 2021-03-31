"""
Tests for FAST-OAD mission viewer
"""
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
from shutil import rmtree

import pandas as pd
import pytest

from ..mission_viewer import MissionViewer

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_mission_viewer(cleanup):
    """
    Basic tests for testing the mission viewer.
    """
    filename = pth.join(DATA_FOLDER_PATH, "flight_points.csv")

    mission_viewer = MissionViewer()

    # Testing with .csv file
    mission_viewer.add_mission(filename, name="Mission 1")

    # Testing with DataFrame
    dataframe = pd.read_csv(filename, index_col=0)
    mission_viewer.add_mission(dataframe, name="Mission 2")

    # Testing with existing .toml
    with pytest.raises(TypeError):
        filename = pth.join(DATA_FOLDER_PATH, "valid_sellar.toml")
        mission_viewer.add_mission(filename, name="Mission 2")

    # Testing display()
    mission_viewer.display()
