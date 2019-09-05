"""
Convenience functions for helping tests
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

import logging
from typing import TypeVar

from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.problem import Problem
from openmdao.core.system import System

from fastoad.openmdao.connections_utils import get_unconnected_inputs

SystemSubclass = TypeVar('SystemSubclass', bound=System)

# Logger for this module
_LOGGER = logging.getLogger(__name__)


def run_system(component: SystemSubclass, input_vars: IndepVarComp, setup_mode='auto'):
    """ Runs and returns an OpenMDAO problem with provided component and data"""
    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('component', component, promotes=['*'])

    problem.setup(mode=setup_mode)
    missing, _ = get_unconnected_inputs(problem, _LOGGER)
    assert not missing

    problem.run_model()

    return problem

def compare_text_files(file1: str, file2: str):
    """
    :param file1: first file.
    :param file2: second file.

    :return: True if text files are the same
    """
    are_same = True
    file1 = open(file1, "r")
    file2 = open(file2, "r")

    l1 = file1.readlines()
    l2 = file2.readlines()

    file1.close()
    file2.close()

    for i, line in enumerate(l1):
        if line != l2[i]:
            are_same = False

    return are_same