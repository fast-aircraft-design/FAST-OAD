"""
Test module for Overall Aircraft Design process
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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
from shutil import rmtree

import openmdao.api as om
import pytest
from numpy.testing import assert_allclose

import fastoad
from fastoad import api
from fastoad.cmd.exceptions import FastFileExistsError
from fastoad.io.configuration import ConfiguredProblem
from fastoad.io.xml import OMLegacy1XmlIO

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), 'results')


@pytest.fixture(scope='module')
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


@pytest.fixture(scope='module')
def install_components():
    """ Needed because other tests play with Pelix/iPOPO """
    fastoad.initialize_framework.load()


def test_propulsion_process(cleanup, install_components):
    """
    Builds a dummy process for finding altitude of min SFC
    """

    problem = ConfiguredProblem()
    problem.configure(pth.join(DATA_FOLDER_PATH, 'propulsion_process.toml'))

    problem.read_inputs()

    problem.setup()
    problem.run_driver()
    problem.write_outputs()

    assert not problem.driver.fail
    assert_allclose(problem.get_val('propulsion:altitude', units='ft'),
                    36700,
                    atol=50)
    assert_allclose(problem.get_val('propulsion:SFC', units='kg/s/N'),
                    1.681e-05,
                    atol=1e-3)


def test_perfo_process(cleanup, install_components):
    """
    Builds a dummy process for finding altitude for max ZFW
    """

    problem = ConfiguredProblem()
    problem.configure(pth.join(DATA_FOLDER_PATH, 'perfo_process.toml'))

    problem.read_inputs()

    problem.setup()
    problem.run_model()
    assert_allclose(problem.get_val('mission:sizing:ZFW', units='kg'),
                    55080,
                    atol=5)
    assert_allclose(problem.get_val('propulsion:SFC', units='kg/s/N'),
                    1.698e-05,
                    atol=1e-3)

    problem.setup()
    problem.run_driver()
    problem.write_outputs()

    assert not problem.driver.fail
    assert_allclose(problem.get_val('mission:sizing:ZFW', units='kg'),
                    55630,
                    atol=10)
    assert_allclose(
        problem.get_val('mission:sizing:cruise:altitude', units='ft'),
        36700,
        atol=100)


def test_oad_process(cleanup, install_components):
    """
    Test for the overall aircraft design process.
    """

    problem = ConfiguredProblem()
    problem.configure(pth.join(DATA_FOLDER_PATH, 'oad_process.toml'))

    problem.setup()
    ref_input_reader = OMLegacy1XmlIO(pth.join(DATA_FOLDER_PATH, 'CeRAS01_baseline.xml'))
    problem.write_needed_inputs(ref_input_reader)
    problem.read_inputs()
    problem.final_setup()
    if not pth.exists(RESULTS_FOLDER_PATH):
        os.mkdir(RESULTS_FOLDER_PATH)
    om.view_connections(problem, outfile=pth.join(RESULTS_FOLDER_PATH, 'connections.html'),
                        show_browser=False)
    om.n2(problem, outfile=pth.join(RESULTS_FOLDER_PATH, 'n2.html'), show_browser=False)
    problem.run_model()

    problem.write_outputs()

    # Check that weight-performances loop correctly converged
    assert_allclose(problem['weight:aircraft:OWE'],
                    problem['weight:airframe:mass'] + problem['weight:propulsion:mass']
                    + problem['weight:systems:mass'] + problem['weight:furniture:mass']
                    + problem['weight:crew:mass'],
                    atol=1)
    assert_allclose(problem['weight:aircraft:MZFW'],
                    problem['weight:aircraft:OWE'] + problem['weight:aircraft:max_payload'],
                    atol=1)
    assert_allclose(problem['weight:aircraft:MTOW'],
                    problem['weight:aircraft:OWE'] + problem['weight:aircraft:payload']
                    + problem['mission:sizing:mission:fuel'],
                    atol=1)


def test_api(cleanup, install_components):
    api_result_folder_path = pth.join(RESULTS_FOLDER_PATH, 'api')
    configuration_file_path = pth.join(api_result_folder_path, 'oad_process.toml')

    # Generation of configuration file ----------------------------------------
    api.generate_configuration_file(configuration_file_path, False)
    # Generating again without forcing overwrite will make it fail
    with pytest.raises(FastFileExistsError):
        api.generate_configuration_file(configuration_file_path, False)
    api.generate_configuration_file(configuration_file_path, True)

    # Generation of inputs ----------------------------------------------------
    source_xml = pth.join(DATA_FOLDER_PATH, 'CeRAS01_baseline.xml')
    api.generate_inputs(configuration_file_path, False, source_xml, 'legacy')
    # Generating again without forcing overwrite will make it fail
    with pytest.raises(FastFileExistsError):
        api.generate_inputs(configuration_file_path, False, source_xml, 'legacy')
    api.generate_inputs(configuration_file_path, True, source_xml, 'legacy')

    # List systems ------------------------------------------------------------
    # TODO: add checks
    api.list_systems(configuration_file_path, pth.join(api_result_folder_path, 'list_systems.txt'))

    # List outputs ------------------------------------------------------------
    # TODO: add checks
    api.list_outputs(configuration_file_path, pth.join(api_result_folder_path, 'list_outputs.txt'))

    # Write N2 ------------------------------------------------------------
    # TODO: add checks
    n2_file_path = pth.join(api_result_folder_path, 'n2.html')
    api.write_n2(configuration_file_path, n2_file_path)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastFileExistsError):
        api.write_n2(configuration_file_path, n2_file_path, False)
    api.write_n2(configuration_file_path, n2_file_path, True)

    # Run model ---------------------------------------------------------------
    api.evaluate_problem(configuration_file_path, False)
    # Running again without forcing overwrite of outputs will make it fail
    with pytest.raises(FastFileExistsError):
        api.evaluate_problem(configuration_file_path, False)
    problem = api.evaluate_problem(configuration_file_path, True)

    # Check that weight-performances loop correctly converged
    assert_allclose(problem['weight:aircraft:OWE'],
                    problem['weight:airframe:mass'] + problem['weight:propulsion:mass']
                    + problem['weight:systems:mass'] + problem['weight:furniture:mass']
                    + problem['weight:crew:mass'],
                    atol=1)
    assert_allclose(problem['weight:aircraft:MZFW'],
                    problem['weight:aircraft:OWE'] + problem['weight:aircraft:max_payload'],
                    atol=1)
    assert_allclose(problem['weight:aircraft:MTOW'],
                    problem['weight:aircraft:OWE'] + problem['weight:aircraft:payload']
                    + problem['mission:sizing:mission:fuel'],
                    atol=1)

    # TODO: check optimization
