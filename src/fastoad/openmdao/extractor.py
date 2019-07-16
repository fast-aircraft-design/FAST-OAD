"""
Extract OpenMDAO elements
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

from logging import Logger
from typing import TypeVar, Tuple, List, Union

import numpy as np
from openmdao.core.problem import Problem
from openmdao.core.system import System
from openmdao.api import IndepVarComp

from fastoad.openmdao.checks import get_unconnected_inputs
from fastoad.exceptions import NoSetupError

from fastoad.openmdao.types import Variable, SystemSubclass

def get_vars_of_unconnected_inputs(problem: Union[Problem, SystemSubclass], logger: Logger = None) -> List[Variable]:
    """
    This function returns an list of Variable containing all the relative
    information of unconnected inputs of a Problem or System.

    :param problem: OpenMDAO Problem or System instance to inspect
    :param logger: optional logger instance
    :return: IndepVarComp Component
    """

    # pylint: disable=protected-access #  needed for OpenMDAO introspection
    if isinstance(problem, Problem):
        model = problem.model
    elif isinstance(problem, System):
        model = problem
    else:
        raise TypeError('Unknown class for retrieving inputs.')
    
    mandatory_unconnected, optional_unconnected = get_unconnected_inputs(model)

    mandatory_unconnected_vars = []
    optional_unconnected_vars = []
    memorize = []
    # Using .list_inputs(), that requires the model to have run
    for (name, attributes) in model.list_inputs(prom_name=True,
                                                    units=True,
                                                    out_stream=None):
        if attributes['prom_name'] not in memorize:
            if name in mandatory_unconnected:
                mandatory_unconnected_vars.append(
                    Variable(attributes['prom_name'], attributes['value'], attributes.get('units', None)))
            else:
                optional_unconnected_vars.append(
                    Variable(attributes['prom_name'], attributes['value'], attributes.get('units', None)))
            memorize.append(attributes['prom_name'])

    return mandatory_unconnected_vars, optional_unconnected_vars


def build_ivc_of_unconnected_inputs(problem: Problem, optional_inputs: bool = False, logger: Logger = None) -> IndepVarComp:
    """
    This function returns an OpenMDAO IndepVarComp Component containing
    all the unconnected inputs of a Problem or System.

    optional_inputs is a Boolean to specify if the IndepVarComp shall contain also the 
    optional inputs.

    :param problem: OpenMDAO Problem instance to inspect
    :param optional_inputs: Boolean for optional inputs
    :param logger: optional logger instance
    :return: IndepVarComp Component
    """

    # pylint: disable=protected-access #  needed for OpenMDAO introspection
    if isinstance(problem, Problem):
        model = problem.model
    elif isinstance(problem, System):
        model = problem
    else:
        raise TypeError('Unknown class for retrieving inputs.')
        
    mandatory_unconnected_vars, optional_unconnected_vars \
        = get_vars_of_unconnected_inputs(problem)

    ivc = IndepVarComp()

    for var in mandatory_unconnected_vars:
        ivc.add_output(var.name, var.value, units=var.units)

    if optional_inputs:
        for var in optional_unconnected_vars:
            ivc.add_output(var.name, var.value, units=var.units)

    return ivc