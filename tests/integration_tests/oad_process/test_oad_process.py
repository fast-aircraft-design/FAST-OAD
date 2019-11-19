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

import os.path as pth
from shutil import rmtree

import numpy as np
import pytest

import fastoad
from fastoad.io.configuration import ConfiguredProblem
from fastoad.io.xml import OMLegacy1XmlIO

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__),
                               'results', pth.splitext(pth.basename(__file__))[0])


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
    np.testing.assert_allclose(problem.get_val('propulsion:altitude', units='ft'),
                               36700,
                               atol=50)
    np.testing.assert_allclose(problem.get_val('propulsion:SFC', units='kg/s/N'),
                               1.681e-05,
                               atol=1e-3)


def test_perfo_process(cleanup, install_components):
    """
    Builds a dummy process for finding altitude for max MZFW
    """

    problem = ConfiguredProblem()
    problem.configure(pth.join(DATA_FOLDER_PATH, 'perfo_process.toml'))

    problem.read_inputs()

    problem.setup()
    problem.run_driver()
    problem.write_outputs()

    assert not problem.driver.fail
    np.testing.assert_allclose(problem.get_val('sizing_mission:cruise_altitude', units='ft'),
                               37500,
                               atol=50)
    np.testing.assert_allclose(problem.get_val('mission:MZFW', units='kg'),
                               55350,
                               atol=50)


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

    problem.run_model()

    problem.write_outputs()

    # TODO: check results
