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
Tests for FAST-OAD variable viewer
"""

import shutil
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from .. import VariableViewer

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results"


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_variable_reader_display():
    """
    Basic tests for testing the VariableReader display method.
    """
    filename = DATA_FOLDER_PATH / "problem_outputs.xml"

    # pylint: disable=invalid-name # that's a common naming
    df = VariableViewer()
    df.load(filename)

    # This is a rudimentary test as ui are difficult to verify
    # The test will fail if an error is raised by the following line
    df.display()


def test_variable_reader_load():
    """
    Basic tests for testing the VariableReader load method.
    """
    col_names = ["Name", "Value", "Unit", "Description", "I/O"]
    ref_df = pd.DataFrame()

    ref_df = pd.concat(
        [
            ref_df,
            pd.DataFrame(
                [
                    {
                        "Name": "data:geometry:cabin:seats:economical:width",
                        "Value": 0.46,
                        "Unit": "m",
                        "Description": "width of economical class seats",
                        "I/O": "IN",
                    },
                    {
                        "Name": "data:geometry:cabin:seats:economical:length",
                        "Value": 0.86,
                        "Unit": "m",
                        "Description": "length of economical class seats",
                        "I/O": "IN",
                    },
                    {
                        "Name": "data:geometry:cabin:aisle_width",
                        "Value": 0.48,
                        "Unit": "m",
                        "Description": "width of aisles",
                        "I/O": "IN",
                    },
                    {
                        "Name": "data:geometry:propulsion:engine:count",
                        "Value": 2.0,
                        "Unit": None,
                        "Description": "number of engines",
                        "I/O": "IN",
                    },
                ]
            ),
        ]
    )[col_names]

    ref_df = ref_df.reset_index(drop=True)

    filename = DATA_FOLDER_PATH / "light_data.xml"

    # Testing file to df
    variable_viewer = VariableViewer()
    variable_viewer.load(filename)

    assert_frame_equal(
        ref_df.sort_values("Name").reset_index(drop=True),
        variable_viewer.dataframe.sort_values("Name").reset_index(drop=True),
    )


def test_variable_reader_save():
    """
    Basic tests for testing the VariableReader save method.
    """
    col_names = ["Name", "Value", "Unit", "Description", "I/O"]
    ref_df = pd.DataFrame()

    ref_df = pd.concat(
        [
            ref_df,
            pd.DataFrame(
                [
                    {
                        "Name": "data:geometry:cabin:seats:economical:width",
                        "Value": 0.46,
                        "Unit": "m",
                        "Description": "width of economical class seats",
                        "I/O": "IN",
                    },
                    {
                        "Name": "data:geometry:cabin:seats:economical:length",
                        "Value": 0.86,
                        "Unit": "m",
                        "Description": "length of economical class seats",
                        "I/O": "IN",
                    },
                    {
                        "Name": "data:geometry:propulsion:engine:count",
                        "Value": 2.0,
                        "Unit": None,
                        "Description": "number of engines",
                        "I/O": "IN",
                    },
                ]
            ),
        ]
    )[col_names]

    ref_df = ref_df.reset_index(drop=True)

    filename = RESULTS_FOLDER_PATH / "light_data.xml"

    # Testing file to df
    variable_viewer = VariableViewer()
    variable_viewer.dataframe = ref_df
    variable_viewer.save(filename)

    # Loading the generated file
    variable_viewer.load(filename)

    assert_frame_equal(
        ref_df.sort_values("Name").reset_index(drop=True),
        variable_viewer.dataframe.sort_values("Name").reset_index(drop=True),
    )
