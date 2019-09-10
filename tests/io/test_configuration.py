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

from fastoad.io.configuration import ConfiguredProblem


def test_problem_definition():
    problem = ConfiguredProblem()
    problem.load(pth.join(pth.dirname(__file__), 'data', 'valid_sellar.toml'))

    problem.driver = om.ScipyOptimizeDriver()
    problem.driver.options['optimizer'] = 'SLSQP'
    problem.setup()

    assert problem.model.group is not None
    assert problem.model.group.disc1 is not None
    assert problem.model.group.disc2 is not None
    assert problem.model.functions is not None
    print(problem.driver.options)
    assert problem.driver.options['optimizer'] == 'SLSQP'
    assert isinstance(problem.model.group.nonlinear_solver, om.NonlinearBlockGS)
