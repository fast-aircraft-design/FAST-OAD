"""
Test module for configuration.py
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
import openmdao.api as om
import pytest

from fastoad.io.configuration import ConfiguredProblem, FASTConfigurationNoProblemDefined, \
    FASTConfigurationBadOpenMDAOInstructionError
from fastoad.io.xml import OMXmlIO

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), 'results')


@pytest.fixture
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_problem_definition(cleanup):
    """ Test problem definition from configuration files """
    # Missing problem
    problem = ConfiguredProblem()
    with pytest.raises(FASTConfigurationNoProblemDefined) as exc_info:
        problem.configure(pth.join(pth.dirname(__file__), 'data', 'missing_problem.toml'))
    assert exc_info is not None

    # Incorrect attribute
    problem = ConfiguredProblem()
    with pytest.raises(FASTConfigurationBadOpenMDAOInstructionError) as exc_info:
        problem.configure(pth.join(pth.dirname(__file__), 'data', 'invalid_attribute.toml'))
        problem.setup_problem()
    assert exc_info is not None
    assert exc_info.value.key == 'problem.cycle.other_group.nonlinear_solver'

    # Reading of correct problem definition
    problem = ConfiguredProblem()
    problem.configure(pth.join(pth.dirname(__file__), 'data', 'valid_sellar.toml'))

    # Just running these methods to check there is no crash. As simple assemblies of
    # other methods, their results should already be unit-tested.
    problem.write_needed_inputs()
    problem.setup_problem()

    assert problem.model.cycle is not None
    assert problem.model.cycle.disc1 is not None
    assert problem.model.cycle.disc2 is not None
    assert problem.model.functions is not None

    assert isinstance(problem.driver, om.ScipyOptimizeDriver)
    assert problem.driver.options['optimizer'] == 'SLSQP'
    assert isinstance(problem.model.cycle.nonlinear_solver, om.NonlinearBlockGS)
    problem.run_driver()

    problem.run_model()
    assert np.isnan(problem['f'])


def test_problem_definition_with_xml_ref(cleanup):
    """ Tests what happens when writing inputs using data from existing XML file"""
    problem = ConfiguredProblem()
    problem.configure(pth.join(DATA_FOLDER_PATH, 'valid_sellar.toml'))

    input_data = OMXmlIO(pth.join(DATA_FOLDER_PATH, 'ref_inputs.xml'))

    problem.write_needed_inputs(input_data)
    problem.setup_problem()

    problem.run_model()
    assert problem['f'] == pytest.approx(28.58830817, abs=1e-6)

    problem.write_outputs()


def test_problem_definition_with_xml_ref_run_optim_mono_fd(cleanup):
    """
    Tests what happens when writing inputs using data from existing XML file
    and running an optimization problem with monolithic FD
    """
    problem = ConfiguredProblem()
    problem.configure(pth.join(DATA_FOLDER_PATH, 'valid_sellar.toml'))

    input_data = OMXmlIO(pth.join(DATA_FOLDER_PATH, 'ref_inputs.xml'))

    problem.write_needed_inputs(input_data)
    problem.setup_problem()

    problem.model.approx_totals()

    problem.run_driver()
    assert problem['f'] == pytest.approx(3.18339395, abs=1e-6)


def test_problem_definition_with_xml_ref_run_semi_fd(cleanup):
    """
    Tests what happens when writing inputs using data from existing XML file
    and running an optimization problem with semi-analytic FD
    """
    problem = ConfiguredProblem()
    problem.configure(pth.join(DATA_FOLDER_PATH, 'valid_sellar.toml'))

    input_data = OMXmlIO(pth.join(DATA_FOLDER_PATH, 'ref_inputs.xml'))

    problem.write_needed_inputs(input_data)
    problem.setup_problem()

    problem.run_driver()
    assert problem['f'] == pytest.approx(3.18339395, abs=1e-6)
