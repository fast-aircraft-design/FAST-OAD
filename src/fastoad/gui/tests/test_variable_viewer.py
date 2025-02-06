"""
Tests for FAST-OAD variable viewer
"""
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

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
import ipysheet as sh

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


def test_sheet_to_df():
    """
    Test for the _sheet_to_df method to ensure it correctly handles data extraction and reshaping,
    including array-like data and integer values.
    """
    # Create a sample ipysheet Sheet
    sheet = sh.sheet(rows=5, columns=4)
    sh.cell(0, 0, 'Name')
    sh.cell(0, 1, 'Value')
    sh.cell(0, 2, 'Unit')
    sh.cell(0, 3, 'Description')
    sh.cell(1, 0, 'data:geometry:cabin:seats:economical:width')
    sh.cell(1, 1, 0.46)
    sh.cell(1, 2, 'm')
    sh.cell(1, 3, 'width of economical class seats')
    sh.cell(2, 0, 'data:geometry:cabin:seats:economical:length')
    sh.cell(2, 1, 0.86)
    sh.cell(2, 2, 'm')
    sh.cell(2, 3, 'length of economical class seats')
    sh.cell(3, 0, 'data:aero:polar:CL')
    sh.cell(3, 1, [0.1, 0.2, 0.3])
    sh.cell(3, 2, None)
    sh.cell(3, 3, 'Lift coefficient')
    sh.cell(4, 0, 'data:geometry:propulsion:engine:count')
    sh.cell(4, 1, 2)
    sh.cell(4, 2, None)
    sh.cell(4, 3, 'number of engines')

    # Convert the sheet to a DataFrame using the _sheet_to_df method
    variable_viewer = VariableViewer()
    df = variable_viewer._sheet_to_df(sheet)

    # Expected DataFrame
    expected_df = pd.DataFrame({
        'Name': [
            'data:geometry:cabin:seats:economical:width',
            'data:geometry:cabin:seats:economical:length',
            'data:aero:polar:CL',
            'data:geometry:propulsion:engine:count'
        ],
        'Value': [0.46, 0.86, [0.1, 0.2, 0.3], 2],
        'Unit': ['m', 'm', None, None],
        'Description': [
            'width of economical class seats',
            'length of economical class seats',
            'Lift coefficient',
            'number of engines'
        ]
    })

    # Assert that the DataFrame matches the expected DataFrame
    assert_frame_equal(df, expected_df)
