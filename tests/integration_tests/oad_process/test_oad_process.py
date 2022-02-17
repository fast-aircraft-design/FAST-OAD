"""
Test module for Overall Aircraft Design process
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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
import shutil
from os import makedirs
from shutil import rmtree

import numpy as np
import openmdao.api as om
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from fastoad.io import DataFile
from fastoad.io.configuration.configuration import (
    FASTOADProblemConfigurator,
)

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_non_regression_mission_only(cleanup):
    run_non_regression_test(
        "oad_process_mission_only.yml",
        "results.xml",
        "non_regression_mission_only",
        specific_tolerance=1.0e-2,
        global_tolerance=10.0e-2,
        check_weight_perfo_loop=False,
    )


def run_non_regression_test(
    conf_file,
    ref_result_file,
    result_dir,
    global_tolerance=1e-2,
    vars_to_check=None,
    specific_tolerance=5.0e-3,
    check_weight_perfo_loop=True,
):
    """
    Convenience function for non regression tests
    :param conf_file: FAST-OAD configuration file
    :param legacy_result_file: reference data for inputs and outputs
    :param result_dir: relative name, folder will be in RESULTS_FOLDER_PATH
    :param use_xfoil: if True, XFOIL computation will be activated
    :param xfoil_path: used if use_xfoil==True
    :param vars_to_check: variables that will be concerned by specific_tolerance
    :param specific_tolerance: test will fail if absolute relative error between computed and
                               reference values is beyond this value for variables in vars_to_check
    :param global_tolerance: test will fail if absolute relative error between computed and
                             reference values is beyond this value for ANY variable
    :param check_weight_perfo_loop: if True, consistency of weights will be checked
    """
    data_folder_path = pth.join(DATA_FOLDER_PATH, result_dir)
    results_folder_path = pth.join(RESULTS_FOLDER_PATH, result_dir)
    makedirs(results_folder_path, exist_ok=True)
    configuration_file_path = pth.join(results_folder_path, conf_file)

    # Copy of configuration file and generation of problem instance ------------------
    shutil.copy(pth.join(data_folder_path, conf_file), configuration_file_path)
    configurator = FASTOADProblemConfigurator(configuration_file_path)

    # Generation of inputs ----------------------------------------
    ref_inputs = pth.join(data_folder_path, ref_result_file)
    configurator.write_needed_inputs(ref_inputs)

    # Get problem with inputs -------------------------------------
    problem = configurator.get_problem(read_inputs=True)
    problem.setup()

    # Run model ---------------------------------------------------------------
    problem.run_model()
    problem.write_outputs()

    om.view_connections(
        problem, outfile=pth.join(results_folder_path, "connections.html"), show_browser=False
    )

    if check_weight_perfo_loop:
        _check_weight_performance_loop(problem)

    ref_data = DataFile(pth.join(data_folder_path, ref_result_file))

    row_list = []
    for ref_var in ref_data:
        try:
            value = problem.get_val(ref_var.name, units=ref_var.units)[0]
        except KeyError:
            continue
        row_list.append(
            {
                "name": ref_var.name,
                "units": ref_var.units,
                "ref_value": ref_var.value[0],
                "value": value,
            }
        )

    df = pd.DataFrame(row_list)
    df["rel_delta"] = (df.value - df.ref_value) / df.ref_value
    df["rel_delta"][(df.ref_value == 0) & (abs(df.value) <= 1e-10)] = 0.0
    df["abs_rel_delta"] = np.abs(df.rel_delta)

    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    pd.set_option("display.max_colwidth", 120)
    print(df.sort_values(by=["abs_rel_delta"]))

    if vars_to_check is not None:
        for name in vars_to_check:
            assert_allclose(df.ref_value, df.value, rtol=global_tolerance)
            row = df.loc[df.name == name]
            assert_allclose(row.ref_value, row.value, rtol=specific_tolerance)
    else:
        assert np.all(df.abs_rel_delta < specific_tolerance)


def _check_weight_performance_loop(problem):
    assert_allclose(
        problem["data:weight:aircraft:OWE"],
        problem["data:weight:airframe:mass"]
        + problem["data:weight:propulsion:mass"]
        + problem["data:weight:systems:mass"]
        + problem["data:weight:furniture:mass"]
        + problem["data:weight:crew:mass"],
        atol=1,
    )
    assert_allclose(
        problem["data:weight:aircraft:MZFW"],
        problem["data:weight:aircraft:OWE"] + problem["data:weight:aircraft:max_payload"],
        atol=1,
    )
    assert_allclose(
        problem["data:weight:aircraft:MTOW"],
        problem["data:weight:aircraft:OWE"]
        + problem["data:weight:aircraft:payload"]
        + problem["data:weight:aircraft:sizing_onboard_fuel_at_takeoff"],
        atol=1,
    )
