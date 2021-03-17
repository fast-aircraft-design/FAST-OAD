"""
Test module for Overall Aircraft Design process
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
from dataclasses import dataclass
from platform import system
from shutil import rmtree

import numpy as np
import openmdao.api as om
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from fastoad import api
from fastoad.io import VariableIO
from fastoad.io.configuration.configuration import (
    FASTOADProblemConfigurator,
    _IConfigurationModifier,
)
from tests import root_folder_path
from tests.xfoil_exe.get_xfoil import get_xfoil_path

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")

xfoil_path = None if system() == "Windows" else get_xfoil_path()


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_oad_process(cleanup):
    """
    Test for the overall aircraft design process.
    """

    configurator = FASTOADProblemConfigurator(pth.join(DATA_FOLDER_PATH, "oad_process.yml"))

    # Create inputs
    ref_inputs = pth.join(DATA_FOLDER_PATH, "CeRAS01_legacy.xml")
    configurator.write_needed_inputs(ref_inputs)

    # Create problems with inputs
    problem = configurator.get_problem(read_inputs=True)
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
        + problem["data:mission:sizing:needed_block_fuel"],
        atol=1,
    )


def test_non_regression_breguet(cleanup):
    run_non_regression_test(
        "oad_process_breguet.yml",
        "CeRAS01_legacy_breguet_result.xml",
        "non_regression_breguet",
        use_xfoil=True,
    )


def test_non_regression_mission_only(cleanup):
    run_non_regression_test(
        "oad_process_mission_only.yml",
        "CeRAS01_legacy_mission_result.xml",
        "non_regression_mission_only",
        use_xfoil=False,
        vars_to_check=["data:mission:sizing:needed_block_fuel"],
        tolerance=1.0e-2,
        check_weight_perfo_loop=False,
    )


def test_non_regression_mission(cleanup):
    run_non_regression_test(
        "oad_process_mission.yml",
        "CeRAS01_legacy_mission_result.xml",
        "non_regression_mission",
        use_xfoil=False,
        vars_to_check=["data:weight:aircraft:MTOW", "data:mission:sizing:fuel"],
        tolerance=1.0e-2,
    )


@dataclass
class XFOILConfigurator(_IConfigurationModifier):
    """Overwrite XFOIL usage setting of configuration file"""

    use_xfoil: bool

    def modify(self, problem: om.Problem):
        if self.use_xfoil and (system() == "Windows" or xfoil_path):
            problem.model.aerodynamics_landing._OPTIONS["use_xfoil"] = True
            if system() != "Windows":
                problem.model.aerodynamics_landing._OPTIONS["xfoil_exe_path"] = xfoil_path
            # BTW we narrow computed alpha range for sake of CPU time
            problem.model.aerodynamics_landing._OPTIONS["xfoil_alpha_min"] = 18.0
            problem.model.aerodynamics_landing._OPTIONS["xfoil_alpha_max"] = 22.0


def run_non_regression_test(
    conf_file,
    legacy_result_file,
    result_dir,
    use_xfoil=False,
    vars_to_check=None,
    tolerance=5.0e-3,
    check_weight_perfo_loop=True,
):
    results_folder_path = pth.join(RESULTS_FOLDER_PATH, result_dir)
    configuration_file_path = pth.join(results_folder_path, conf_file)

    # Copy of configuration file and generation of problem instance ------------------
    api.generate_configuration_file(configuration_file_path)  # just ensure folders are created...
    shutil.copy(pth.join(DATA_FOLDER_PATH, conf_file), configuration_file_path)
    configurator = FASTOADProblemConfigurator(configuration_file_path)
    configurator._set_configuration_modifier(XFOILConfigurator(use_xfoil))

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
        # Check that weight-performances loop correctly converged
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
            + problem["data:mission:sizing:needed_block_fuel"],
            atol=1,
        )

    ref_var_list = VariableIO(pth.join(DATA_FOLDER_PATH, legacy_result_file),).read()

    row_list = []
    for ref_var in ref_var_list:
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
            row = df.loc[df.name == name]
            assert_allclose(row.ref_value, row.value, rtol=tolerance)
            # assert np.all(df.abs_rel_delta.loc[df.name == name] < tolerance)
    else:
        assert np.all(df.abs_rel_delta < tolerance)


def test_api_eval(cleanup):
    results_folder_path = pth.join(RESULTS_FOLDER_PATH, "api_eval")
    configuration_file_path = pth.join(results_folder_path, "oad_process.yml")

    # Generation of configuration file ----------------------------------------
    api.generate_configuration_file(configuration_file_path, True)

    # Generation of inputs ----------------------------------------------------
    # We get the same inputs as in tutorial notebook
    source_xml = pth.join(
        root_folder_path, "src", "fastoad", "notebooks", "tutorial", "data", "CeRAS01_baseline.xml"
    )
    api.generate_inputs(configuration_file_path, source_xml, overwrite=True)

    # Run model ---------------------------------------------------------------
    problem = api.evaluate_problem(configuration_file_path, True)

    # Check that weight-performances loop correctly converged
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
        + problem["data:mission:sizing:needed_block_fuel"],
        atol=1,
    )

    assert_allclose(problem["data:handling_qualities:static_margin"], -0.071146, atol=1e-3)
    assert_allclose(problem["data:geometry:wing:MAC:at25percent:x"], 16.0, atol=1e-2)
    assert_allclose(problem["data:weight:aircraft:MTOW"], 76796, atol=1)
    assert_allclose(problem["data:geometry:wing:area"], 131.26, atol=1e-2)
    assert_allclose(problem["data:geometry:vertical_tail:area"], 27.49, atol=1e-2)
    assert_allclose(problem["data:geometry:horizontal_tail:area"], 33.99, atol=1e-2)
    assert_allclose(problem["data:mission:sizing:needed_block_fuel"], 20708, atol=1)


def test_api_optim(cleanup):
    results_folder_path = pth.join(RESULTS_FOLDER_PATH, "api_optim")
    configuration_file_path = pth.join(results_folder_path, "oad_process.toml")

    # Generation of configuration file ----------------------------------------
    api.generate_configuration_file(configuration_file_path, True)

    # Generation of inputs ----------------------------------------------------
    # We get the same inputs as in tutorial notebook
    source_xml = pth.join(
        root_folder_path, "src", "fastoad", "notebooks", "tutorial", "data", "CeRAS01_baseline.xml"
    )
    api.generate_inputs(configuration_file_path, source_xml, overwrite=True)

    # Run optim ---------------------------------------------------------------
    problem = api.optimize_problem(configuration_file_path, True)
    assert not problem.optim_failed

    # Check that weight-performances loop correctly converged
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
        + problem["data:mission:sizing:needed_block_fuel"],
        atol=1,
    )

    # Design Variable
    assert_allclose(problem["data:geometry:wing:MAC:at25percent:x"], 17.06, atol=1e-1)

    # Constraint
    assert_allclose(problem["data:handling_qualities:static_margin"], 0.05, atol=1e-2)

    # Objective
    assert_allclose(problem["data:mission:sizing:needed_block_fuel"], 20837, atol=50)
