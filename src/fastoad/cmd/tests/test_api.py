"""
Tests for basic API
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

import os
import os.path as pth
import shutil
from filecmp import cmp
from shutil import rmtree

import pytest

import fastoad.models
from fastoad.openmdao.variables import Variable
from .. import api
from ..api import SAMPLE_FILENAME
from ..exceptions import FastFileExistsError

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")
CONFIGURATION_FILE_PATH = pth.join(DATA_FOLDER_PATH, "sellar.yml")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)

    # Need to clean up variable descriptions because it is manipulated in other tests.
    Variable.read_variable_descriptions(pth.dirname(fastoad.models.__file__), update_existing=False)


def test_generate_configuration_file(cleanup):
    configuration_file_path = pth.join(RESULTS_FOLDER_PATH, "new_process.yml")

    api.generate_configuration_file(configuration_file_path, False)
    # Generating again without forcing overwrite will make it fail
    with pytest.raises(FastFileExistsError):
        api.generate_configuration_file(configuration_file_path, False)
    api.generate_configuration_file(configuration_file_path, True)

    original_file = pth.join(pth.dirname(api.__file__), "resources", SAMPLE_FILENAME)
    assert cmp(configuration_file_path, original_file)


def test_generate_inputs(cleanup):
    api.generate_inputs(CONFIGURATION_FILE_PATH, overwrite=False)
    # Generating again without forcing overwrite will make it fail
    with pytest.raises(FastFileExistsError):
        api.generate_inputs(CONFIGURATION_FILE_PATH, overwrite=False)
    input_file_path = api.generate_inputs(
        CONFIGURATION_FILE_PATH, pth.join(DATA_FOLDER_PATH, "inputs.xml"), overwrite=True
    )
    assert input_file_path == pth.join(RESULTS_FOLDER_PATH, "inputs.xml")
    assert pth.exists(input_file_path)


def test_list_modules(cleanup):
    # Run with stdout output (no test)
    api.list_modules()
    api.list_modules(CONFIGURATION_FILE_PATH, verbose=True)
    api.list_modules(CONFIGURATION_FILE_PATH, verbose=False)

    # Run with file output (test file existence)
    out_file = pth.join(RESULTS_FOLDER_PATH, "list_modules.txt")
    assert not pth.exists(out_file)
    api.list_modules(CONFIGURATION_FILE_PATH, out_file)
    with pytest.raises(FastFileExistsError):
        api.list_modules(CONFIGURATION_FILE_PATH, out_file)
    api.list_modules(CONFIGURATION_FILE_PATH, out_file, overwrite=True)

    assert pth.exists(out_file)


def test_list_variables(cleanup):
    # Run with stdout output (no test)
    api.list_variables(CONFIGURATION_FILE_PATH)

    # Run with file output (test file existence)
    out_file_path = pth.join(RESULTS_FOLDER_PATH, "list_variables.txt")
    assert not pth.exists(out_file_path)
    api.list_variables(CONFIGURATION_FILE_PATH, out=out_file_path)
    with pytest.raises(FastFileExistsError):
        api.list_variables(CONFIGURATION_FILE_PATH, out=out_file_path)
    api.list_variables(CONFIGURATION_FILE_PATH, out=out_file_path, overwrite=True)
    assert pth.exists(out_file_path)

    ref_file_path = pth.join(DATA_FOLDER_PATH, "ref_list_variables.txt")
    assert cmp(ref_file_path, out_file_path)


def test_write_n2(cleanup):

    n2_file_path = pth.join(RESULTS_FOLDER_PATH, "other_n2.html")
    api.write_n2(CONFIGURATION_FILE_PATH, n2_file_path)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastFileExistsError):
        api.write_n2(CONFIGURATION_FILE_PATH, n2_file_path, False)
    api.write_n2(CONFIGURATION_FILE_PATH, n2_file_path, True)
    assert pth.exists(n2_file_path)


@pytest.mark.skip("This test requires access to the WhatsOpt server")
def test_write_xdsm(cleanup):
    default_xdsm_file_path = pth.join(DATA_FOLDER_PATH, "xdsm.html")
    api.write_xdsm(CONFIGURATION_FILE_PATH)
    assert pth.exists(default_xdsm_file_path)
    os.remove(default_xdsm_file_path)

    xdsm_file_path = pth.join(RESULTS_FOLDER_PATH, "other_xdsm.html")
    api.write_xdsm(CONFIGURATION_FILE_PATH, xdsm_file_path)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastFileExistsError):
        api.write_xdsm(CONFIGURATION_FILE_PATH, xdsm_file_path, False)
    api.write_xdsm(CONFIGURATION_FILE_PATH, xdsm_file_path, True)
    assert pth.exists(xdsm_file_path)


def test_evaluate_problem(cleanup):
    api.generate_inputs(
        CONFIGURATION_FILE_PATH, pth.join(DATA_FOLDER_PATH, "inputs.xml"), overwrite=True
    )
    api.evaluate_problem(CONFIGURATION_FILE_PATH, False)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastFileExistsError):
        api.evaluate_problem(CONFIGURATION_FILE_PATH, False)
    problem = api.evaluate_problem(CONFIGURATION_FILE_PATH, True)
    assert problem["f"] == pytest.approx(32.56910089, abs=1e-8)

    # Move output file because it will be overwritten by the optim test
    shutil.move(
        pth.join(RESULTS_FOLDER_PATH, "outputs.xml"),
        pth.join(RESULTS_FOLDER_PATH, "outputs_eval.xml"),
    )


def test_optimize_problem(cleanup):
    api.generate_inputs(
        CONFIGURATION_FILE_PATH, pth.join(DATA_FOLDER_PATH, "inputs.xml"), overwrite=True
    )
    api.optimize_problem(CONFIGURATION_FILE_PATH, False)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastFileExistsError):
        api.optimize_problem(CONFIGURATION_FILE_PATH, False)
    problem = api.optimize_problem(CONFIGURATION_FILE_PATH, True)

    assert problem["f"] == pytest.approx(3.18339395, abs=1e-8)


def test_optimization_viewer(cleanup):
    api.generate_inputs(
        CONFIGURATION_FILE_PATH, pth.join(DATA_FOLDER_PATH, "inputs.xml"), overwrite=True
    )

    # Before a run
    api.optimization_viewer(CONFIGURATION_FILE_PATH)

    api.optimize_problem(CONFIGURATION_FILE_PATH, True)

    # After a run
    api.optimization_viewer(CONFIGURATION_FILE_PATH)


def test_variable_viewer(cleanup):

    file_path = pth.join(DATA_FOLDER_PATH, "short_inputs.xml")

    # Using default file formatter
    api.variable_viewer(file_path)

    api.variable_viewer(file_path, editable=False)
