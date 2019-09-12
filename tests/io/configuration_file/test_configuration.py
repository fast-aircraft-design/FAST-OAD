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

import openmdao.api as om
import pytest

from fastoad.io.configuration import ConfiguredProblem, FASTConfigurationNoProblemDefined, \
    FASTConfigurationBadOpenMDAOInstructionError


def test_problem_definition():
    # Reading of correct problem definition
    problem = ConfiguredProblem()
    problem.configure(pth.join(pth.dirname(__file__), 'data', 'valid_sellar.toml'))

    problem.setup()

    assert problem.model.cycle is not None
    assert problem.model.cycle.disc1 is not None
    assert problem.model.cycle.disc2 is not None
    assert problem.model.functions is not None

    assert isinstance(problem.driver, om.ScipyOptimizeDriver)
    assert problem.driver.options['optimizer'] == 'SLSQP'
    assert isinstance(problem.model.cycle.nonlinear_solver, om.NonlinearBlockGS)

    # Missing problem
    problem = ConfiguredProblem()
    with pytest.raises(FASTConfigurationNoProblemDefined) as exc_info:
        problem.configure(pth.join(pth.dirname(__file__), 'data', 'missing_problem.toml'))
    assert exc_info is not None

    # Incorrect attribute
    problem = ConfiguredProblem()
    with pytest.raises(FASTConfigurationBadOpenMDAOInstructionError) as exc_info:
        problem.configure(pth.join(pth.dirname(__file__), 'data', 'invalid_attribute.toml'))
    assert exc_info is not None
    assert exc_info.value.key == 'problem.cycle.other_group.nonlinear_solver'
