# This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
# Copyright (c) 2025 ONERA & ISAE-SUPAERO
# FAST-OAD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for FAST-OAD mission viewer
"""

from pathlib import Path

import pandas as pd
import pytest

from ..mission_viewer import MissionViewer

DATA_FOLDER_PATH = Path(__file__).parent / "data"


def test_mission_viewer():
    """
    Basic tests for testing the mission viewer.
    """
    filename = DATA_FOLDER_PATH / "flight_points.csv"

    mission_viewer = MissionViewer()

    # Testing with .csv file
    mission_viewer.add_mission(filename, name="Mission 1")

    # Testing with DataFrame
    dataframe = pd.read_csv(filename, index_col=0)
    mission_viewer.add_mission(dataframe, name="Mission 2")

    # Testing with existing .yml
    with pytest.raises(TypeError):
        filename = DATA_FOLDER_PATH / "valid_sellar.yml"
        mission_viewer.add_mission(filename, name="Mission 2")


def test_mission_display():
    """
    Basic tests for testing the display of the mission viewer which ensures that altitude and
    ground distance are displayed by default
    """

    # Testing with a .csv file
    filename = DATA_FOLDER_PATH / "flight_points.csv"

    mission_viewer = MissionViewer()

    mission_viewer.add_mission(filename)

    mission_viewer.display()

    assert mission_viewer._x_widget.value == "ground_distance [m]"
    assert mission_viewer._y_widget.value == "altitude [m]"

    # Testing with a disorganised .csv file since it seeks the right indices
    filename = DATA_FOLDER_PATH / "flight_points_disorganised.csv"

    mission_viewer = MissionViewer()
    mission_viewer.add_mission(filename)

    mission_viewer.display()

    assert mission_viewer._x_widget.value == "ground_distance [m]"
    assert mission_viewer._y_widget.value == "altitude [m]"

    # Testing with a disorganised .csv file and a missing column
    filename = DATA_FOLDER_PATH / "flight_points_disorganised_missing_column.csv"

    mission_viewer = MissionViewer()
    mission_viewer.add_mission(filename)

    mission_viewer.display()

    assert mission_viewer._x_widget.value == "consumed_fuel [kg]"
    # It's missing the ground distance column so it will use the column at index 1
    assert mission_viewer._y_widget.value == "altitude [m]"


def test_mission_layout():
    """
    Basic tests for testing the mission viewer layout update functionality
    """
    filename = DATA_FOLDER_PATH / "flight_points.csv"

    mission_viewer = MissionViewer()

    mission_viewer.add_mission(filename, name="Mission 1")

    # Testing layout update with dictionary
    mission_viewer.display({"title": None})

    # Testing layout update with keywords
    mission_viewer.display(title_text="Title")

    # Testing layout overwrite = True
    mission_viewer.display(layout_overwrite=True, title_text="mission")
