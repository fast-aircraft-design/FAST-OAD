"""
Tests for FAST-OAD optimization viewer
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
from shutil import rmtree, copyfile

import pytest
from fastoad.cmd import api
from fastoad.io.configuration.configuration import FASTOADProblemConfigurator

from .. import OptimizationViewer
from ..exceptions import FastMissingFile

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_optimization_viewer_load(cleanup):
    """
    Basic tests for testing the OptimizationViewer load method.
    """
    filename = pth.join(DATA_FOLDER_PATH, "valid_sellar.toml")

    # The problem has not yet been run
    problem_configuration = FASTOADProblemConfigurator(filename)

    optim_viewer = OptimizationViewer()

    # No input file exists
    with pytest.raises(FastMissingFile):
        optim_viewer.load(problem_configuration)

    api.generate_inputs(filename, pth.join(DATA_FOLDER_PATH, "inputs.xml"), overwrite=True)

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
    filename = pth.join(DATA_FOLDER_PATH, "valid_sellar.toml")
    new_filename = pth.join(RESULTS_FOLDER_PATH, "new_valid_sellar.toml")
    copyfile(filename, new_filename)

    # Loading new file
    problem_configuration = FASTOADProblemConfigurator(filename)

    optim_viewer = OptimizationViewer()

    api.generate_inputs(new_filename, pth.join(DATA_FOLDER_PATH, "inputs.xml"), overwrite=True)

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
    filename = pth.join(DATA_FOLDER_PATH, "valid_sellar.toml")

    # The problem has not yet been ran
    problem_configuration = FASTOADProblemConfigurator(filename)

    optim_viewer = OptimizationViewer()

    api.generate_inputs(filename, pth.join(DATA_FOLDER_PATH, "inputs.xml"), overwrite=True)

    optim_viewer.load(problem_configuration)
    optim_viewer.display()
