"""
Test module for Overall Aircraft Design process
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

import os
import os.path as pth
import shutil
from dataclasses import dataclass
from platform import system
from shutil import rmtree

import numpy as np
import openmdao.api as om
import pandas as pd
import pytest
from numpy.testing import assert_allclose

import fastoad.api as oad
from fastoad.io.configuration.configuration import (
    FASTOADProblemConfigurator,
    _IConfigurationModifier,
)

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_oad_process(cleanup):
    """
    Test for the overall aircraft design process.
    """

    configurator = FASTOADProblemConfigurator(pth.join(DATA_FOLDER_PATH, "oad_process.yml"))

    ref_inputs = pth.join(DATA_FOLDER_PATH, "CeRAS01_legacy.xml")
    problem = configurator.get_problem()
    problem.write_needed_inputs(ref_inputs)
    problem.read_inputs()

    problem.setup()
    problem.run_model()
    problem.write_outputs()

    if not pth.exists(RESULTS_FOLDER_PATH):
        os.mkdir(RESULTS_FOLDER_PATH)
    om.view_connections(
        problem, outfile=pth.join(RESULTS_FOLDER_PATH, "connections.html"), show_browser=False
    )
    om.n2(problem, outfile=pth.join(RESULTS_FOLDER_PATH, "n2.html"), show_browser=False)

    # Check that weight-performances loop correctly converged
    _check_weight_performance_loop(problem)


def test_non_regression_breguet(cleanup, xfoil_path):
    run_non_regression_test(
        "oad_process_breguet.yml",
        "CeRAS01_legacy_breguet_result.xml",
        "non_regression_breguet",
        use_xfoil=True,
        xfoil_path=xfoil_path,
    )


def test_non_regression_mission_only(cleanup):
    run_non_regression_test(
        "oad_process_mission_only.yml",
        "CeRAS01_legacy_mission_only_result.xml",
        "non_regression_mission_only",
        use_xfoil=False,
        vars_to_check=["data:mission:sizing:needed_block_fuel"],
        specific_tolerance=1.0e-2,
        global_tolerance=10.0e-2,
        check_weight_perfo_loop=False,
    )


@dataclass
class XFOILConfigurator(_IConfigurationModifier):
    """Overwrite XFOIL usage setting of configuration file"""

    use_xfoil: bool
    xfoil_path: str = None

    def modify(self, problem: om.Problem):
        if self.use_xfoil and (system() == "Windows" or self.xfoil_path):
            problem.model.aerodynamics_landing._OPTIONS["use_xfoil"] = True
            if system() != "Windows":
                problem.model.aerodynamics_landing._OPTIONS["xfoil_exe_path"] = self.xfoil_path
            # BTW we narrow computed alpha range for sake of CPU time
            problem.model.aerodynamics_landing._OPTIONS["xfoil_alpha_min"] = 16.0
            problem.model.aerodynamics_landing._OPTIONS["xfoil_alpha_max"] = 22.0


def run_non_regression_test(
    conf_file,
    legacy_result_file,
    result_dir,
    use_xfoil=False,
    xfoil_path=None,
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
    results_folder_path = pth.join(RESULTS_FOLDER_PATH, result_dir)
    configuration_file_path = pth.join(results_folder_path, conf_file)

    # Copy of configuration file and generation of problem instance ------------------
    oad.generate_configuration_file(configuration_file_path)  # just ensure folders are created...
    shutil.copy(pth.join(DATA_FOLDER_PATH, conf_file), configuration_file_path)
    configurator = FASTOADProblemConfigurator(configuration_file_path)
    configurator._set_configuration_modifier(XFOILConfigurator(use_xfoil, xfoil_path))

    # Generation of inputs ----------------------------------------
    ref_inputs = pth.join(DATA_FOLDER_PATH, legacy_result_file)
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

    ref_data = oad.DataFile(pth.join(DATA_FOLDER_PATH, legacy_result_file))

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

    assert_allclose(df.value, df.ref_value, rtol=global_tolerance, atol=1.0e-9)
    if vars_to_check is not None:
        for name in vars_to_check:
            row = df.loc[df.name == name]
            assert_allclose(row.value, row.ref_value, rtol=specific_tolerance, atol=1.0e-9)


def test_api_eval_breguet(cleanup):
    results_folder_path = pth.join(RESULTS_FOLDER_PATH, "api_eval_breguet")
    configuration_file_path = pth.join(results_folder_path, "oad_process.yml")

    # Generation of configuration file ----------------------------------------
    oad.generate_configuration_file(configuration_file_path, True)

    # Generation of inputs ----------------------------------------------------
    # We get the same inputs as in tutorial notebook
    source_xml = pth.join(DATA_FOLDER_PATH, "CeRAS01_notebooks.xml")
    oad.generate_inputs(configuration_file_path, source_xml, overwrite=True)

    # Run model ---------------------------------------------------------------
    problem = oad.evaluate_problem(configuration_file_path, True)

    # Check that weight-performances loop correctly converged
    _check_weight_performance_loop(problem)

    assert_allclose(problem["data:handling_qualities:static_margin"], 0.05, atol=1e-2)
    assert_allclose(problem["data:geometry:wing:MAC:at25percent:x"], 17.149, atol=1e-2)
    assert_allclose(problem["data:weight:aircraft:MTOW"], 74892, atol=1)
    assert_allclose(problem["data:geometry:wing:area"], 126.732, atol=1e-2)
    assert_allclose(problem["data:geometry:vertical_tail:area"], 27.565, atol=1e-2)
    assert_allclose(problem["data:geometry:horizontal_tail:area"], 35.884, atol=1e-2)
    assert_allclose(problem["data:mission:sizing:needed_block_fuel"], 19527, atol=1)

    _run_plots(problem.output_file_path)


def test_api_optim(cleanup):
    results_folder_path = pth.join(RESULTS_FOLDER_PATH, "api_optim")
    configuration_file_path = pth.join(results_folder_path, "oad_process.yml")

    # Generation of configuration file ----------------------------------------
    oad.generate_configuration_file(configuration_file_path, True)

    # Generation of inputs ----------------------------------------------------
    # We get the same inputs as in tutorial notebook
    source_xml = pth.join(DATA_FOLDER_PATH, "CeRAS01_notebooks.xml")
    oad.generate_inputs(configuration_file_path, source_xml, overwrite=True)

    # Run optim ---------------------------------------------------------------
    problem = oad.optimize_problem(configuration_file_path, True)
    assert not problem.optim_failed

    # Check that weight-performances loop correctly converged
    _check_weight_performance_loop(problem)

    # Design Variable
    assert_allclose(problem["data:geometry:wing:aspect_ratio"], 14.53, atol=2e-2)

    # Constraint
    assert_allclose(problem["data:geometry:wing:span"], 44.88, atol=2e-2)

    # Objective
    assert_allclose(problem["data:mission:sizing:needed_block_fuel"], 18900.0, atol=1)


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
        + problem["data:weight:aircraft:sizing_onboard_fuel_at_input_weight"],
        atol=1,
    )


def _run_plots(xml_file_path: str):
    oad.wing_geometry_plot(xml_file_path)
    oad.aircraft_geometry_plot(xml_file_path)
    oad.mass_breakdown_bar_plot(xml_file_path)
    oad.mass_breakdown_sun_plot(xml_file_path)
    oad.drag_polar_plot(xml_file_path)
