"""
Tests for FAST-OAD optimization viewer
"""

import shutil
from pathlib import Path

import pytest

from fastoad.cmd import api
from fastoad.io.configuration.configuration import FASTOADProblemConfigurator

from .. import OptimizationViewer
from ..exceptions import FastMissingFile

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
    with pytest.raises(FastMissingFile):
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
