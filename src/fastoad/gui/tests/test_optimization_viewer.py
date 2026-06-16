"""
Tests for FAST-OAD optimization viewer
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

from fastoad.cmd import api
from fastoad.io.configuration.configuration import FASTOADProblemConfigurator

from .. import OptimizationViewer
from ..exceptions import FastMissingFileError

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results"


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_optimization_viewer_load(cleanup):
    """
    Basic tests for testing the OptimizationViewer load method.
    """
    filename = DATA_FOLDER_PATH / "valid_sellar.yml"

    # The problem has not yet been run
    problem_configuration = FASTOADProblemConfigurator(filename)

    optim_viewer = OptimizationViewer()

    # No input file exists
    with pytest.raises(FastMissingFileError):
        optim_viewer.load(problem_configuration)

    api.generate_inputs(filename, DATA_FOLDER_PATH / "inputs.xml", overwrite=True)

    # Input file exist
    optim_viewer.load(problem_configuration)

    # We run the problem
    api.optimize_problem(filename, overwrite=True)

    # Load the results
    optim_viewer.load(problem_configuration)


def test_optimization_viewer_save(cleanup):
    """
    Basic tests for testing the OptimizationViewer save method.
    """
    filename = DATA_FOLDER_PATH / "valid_sellar.yml"
    new_filename = RESULTS_FOLDER_PATH / "new_valid_sellar.yml"
    shutil.copy(filename, new_filename)

    # Loading new file
    problem_configuration = FASTOADProblemConfigurator(new_filename)

    optim_viewer = OptimizationViewer()

    api.generate_inputs(new_filename, DATA_FOLDER_PATH / "inputs.xml", overwrite=True)

    # Load new file
    optim_viewer.load(problem_configuration)
    optim_viewer.save()
    optim_viewer.load(problem_configuration)

    # We run the problem
    api.optimize_problem(new_filename, overwrite=True)
    optim_viewer.load(problem_configuration)
    optim_viewer.save()
    optim_viewer.load(problem_configuration)


def test_optimization_viewer_display(cleanup):
    """
    Basic tests for testing the OptimizationViewer load method.
    """
    filename = DATA_FOLDER_PATH / "valid_sellar.yml"

    # The problem has not yet been ran
    problem_configuration = FASTOADProblemConfigurator(filename)

    optim_viewer = OptimizationViewer()

    api.generate_inputs(filename, DATA_FOLDER_PATH / "inputs.xml", overwrite=True)

    optim_viewer.load(problem_configuration)
    optim_viewer.display()


def test_update_callback_persists_editable_and_reverts_readonly():
    """The ``on_cell_change`` callback persists edits to editable columns and
    reverts edits to read-only columns (ipydatagrid has no per-column editable
    flag), so the grid cannot diverge from ``self.dataframe``.
    """

    class _FakeGrid:
        def __init__(self):
            self.reverted = []

        def set_cell_value(self, col, row, value):
            self.reverted.append((col, row, value))

    optim_viewer = OptimizationViewer()
    optim_viewer.dataframe = pd.DataFrame(
        {"Name": ["x"], "Value": [3.0], "Lower": [0.0], "Upper": [10.0]}
    )

    grid = _FakeGrid()
    callback = optim_viewer._make_update_callback([0], grid)

    # An editable column is persisted (and converted to float).
    callback({"row": 0, "column": "Lower", "value": "1.5"})
    assert optim_viewer.dataframe.loc[0, "Lower"] == pytest.approx(1.5)
    assert grid.reverted == []

    # A read-only column is reverted and the dataframe is left untouched.
    callback({"row": 0, "column": "Name", "value": "HACKED"})
    assert optim_viewer.dataframe.loc[0, "Name"] == "x"
    assert grid.reverted == [("Name", 0, "x")]
