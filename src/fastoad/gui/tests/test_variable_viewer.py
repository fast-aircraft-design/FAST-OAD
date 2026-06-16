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

import numpy as np
import pandas as pd
import pytest
from ipydatagrid import DataGrid
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


def test_variable_viewer_with_arrays():
    """
    VariableViewer must not raise a ValueError when the XML file contains
    variables whose values are arrays (mixed scalar / array types in the
    Value column used to break dataframe serialisation).
    """
    # problem_outputs.xml contains both scalar and array-valued variables
    filename = DATA_FOLDER_PATH / "problem_outputs.xml"

    viewer = VariableViewer()
    viewer.load(filename)

    # display() must not raise
    viewer.display()

    # At least one array-valued variable must be present to make the test meaningful
    has_array = viewer.dataframe["Value"].apply(
        lambda v: isinstance(v, (list, np.ndarray)) and len(v) > 1
    )
    assert has_array.any(), "Test data must contain at least one array-valued variable"

    # The grid must be a DataGrid instance
    assert isinstance(viewer._grid, DataGrid)

    # get_variables() must still round-trip without error
    variables = viewer.get_variables()
    assert len(variables) > 0


def test_value_to_display_and_back():
    """Unit tests for the array from/to string conversion helpers."""
    # numpy array round-trip
    arr = np.array([1.0, 2.0, 3.0])
    display_val = VariableViewer._value_to_display(arr)
    assert isinstance(display_val, str)
    recovered = VariableViewer._display_to_value(display_val, arr)
    np.testing.assert_array_almost_equal(recovered, arr)

    # list round-trip (the actual storage type used by VariableIO)
    lst = [1.0, 2.0, 3.0]
    display_val = VariableViewer._value_to_display(lst)
    assert isinstance(display_val, str)
    recovered = VariableViewer._display_to_value(display_val, lst)
    assert recovered == lst

    # Scalar values are preserved as-is
    assert VariableViewer._value_to_display(3.14) == 3.14
    assert VariableViewer._display_to_value("2.5", 1.0) == pytest.approx(2.5)


def test_display_to_value_array_edited_to_scalar_falls_back():
    """
    Replacing an array-valued cell by a scalar string must not raise.

    ``ast.literal_eval("1.0")`` returns a float, which cannot be cast back into a
    list/tuple (``list(1.0)`` raises ``TypeError``). In that case the original
    value must be kept rather than letting the exception propagate.
    """
    original_list = [1.0, 2.0, 3.0]
    assert VariableViewer._display_to_value("1.0", original_list) == original_list

    original_tuple = (1.0, 2.0)
    assert VariableViewer._display_to_value("5", original_tuple) == original_tuple


def test_update_df_persists_value_and_reverts_readonly_edits():
    """
    ``_update_df`` persists edits to the *Value* column and reverts edits to
    read-only columns so the grid cannot diverge from ``self.dataframe``.
    """
    df = pd.DataFrame(
        {
            "Name": ["a", "b"],
            "Value": [1.0, 2.0],
            "Unit": ["m", "m"],
            "Description": ["", ""],
            "I/O": ["IN", "OUT"],
        }
    )
    viewer = VariableViewer()
    viewer.dataframe = df.copy()
    viewer._filtered_indices = [0, 1]
    viewer._grid = VariableViewer._df_to_grid(df)

    # Spy on set_cell_value to confirm read-only edits are reverted in the grid.
    reverted = []
    viewer._grid.set_cell_value = lambda col, row, val: reverted.append((col, row, val))

    # Editing the Value column is persisted.
    viewer._update_df({"row": 0, "column": "Value", "value": "9.0"})
    assert viewer.dataframe.loc[0, "Value"] == pytest.approx(9.0)
    assert reverted == []

    # Editing a read-only column leaves the dataframe untouched and reverts the grid.
    viewer._update_df({"row": 1, "column": "Name", "value": "HACKED"})
    assert viewer.dataframe.loc[1, "Name"] == "b"
    assert reverted == [("Name", 1, "b")]
