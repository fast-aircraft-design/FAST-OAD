"""
Utility functions for OpenMDAO classes/instances
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

from fastoad.exceptions import NoSetupError

from fastoad.openmdao.types import Variable, SystemSubclass


def get_unconnected_inputs(problem: Union[Problem, SystemSubclass], logger: Logger = None) -> Tuple[List[str], List[str]]:
    """
    For provided OpenMDAO problem, looks for inputs that are connected to no output.
    Assumes problem.setup() has been run.

    Inputs that have numpy.nan as default value are considered as mandatory. Other ones are
    considered as optional.

    If a logger is provided, it will issue errors for the first category, and warnings for the
    second one.

    :param problem: OpenMDAO Problem or System instance to inspect
    :param logger: optional logger instance
    :return: tuple(list of missing mandatory inputs, list of missing optional inputs)
    """

    # pylint: disable=protected-access #  needed for OpenMDAO introspection
    if isinstance(problem, Problem):
        model = problem.model
    elif isinstance(problem, System):
        model = problem
    else:
        raise TypeError('Unknown class for retrieving inputs.')

    if not model._var_allprocs_prom2abs_list:
        raise NoSetupError('Analysis of unconnected inputs cannot be done without prior setup.')

    prom2abs: dict = model._var_allprocs_prom2abs_list['input']
    connexions: dict = model._conn_global_abs_in2out

    mandatory_unconnected = []
    optional_unconnected = []

    for abs_names in prom2abs.values():
        # At each iteration, get absolute names that match one promoted name, or one
        # absolute name that has not been promoted.
        unconnected = [a for a in abs_names if a not in connexions or len(connexions[a]) == 0]
        if unconnected:
            for abs_name in abs_names:
                value = _get_value_from_absolute_name(model, abs_name)
                if np.all(np.isnan(value)):
                    mandatory_unconnected.append(abs_name)
                else:
                    optional_unconnected.append(abs_name)

    if logger:
        if mandatory_unconnected:
            logger.error('Following inputs are required and not connected:')
            for abs_name in sorted(mandatory_unconnected):
                logger.error('    %s', abs_name)

        if optional_unconnected:
            logger.warning(
                'Following inputs are not connected so their default value will be used:')
            for abs_name in sorted(optional_unconnected):
                value = _get_value_from_absolute_name(model, abs_name)
                logger.warning('    %s : %s', abs_name, value)

    return mandatory_unconnected, optional_unconnected


def _get_value_from_absolute_name(system: SystemSubclass, name):
    """

    :param system: any OpenMDAO system instance
    :param name: absolute name of OpenMDAO variable
    :return: currently associated value to identified variable, or None if variable could not be
             found.
    """
    # pylint: disable=protected-access #  needed for OpenMDAO introspection
    if name in system._var_abs2meta:
        metadata: dict = system._var_abs2meta[name]
        return metadata.get('value')

    return None

def get_vars_of_unconnected_inputs(problem: Union[Problem, SystemSubclass], logger: Logger = None) -> List[Variable]:
    """
    This function returns a list of Variable containing all the relative
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
    prom2abs = model._var_allprocs_prom2abs_list['input']

    for prom_name in prom2abs.keys():
        # Pick first abs_name
        abs_name = prom2abs[prom_name][0]
        meta = model._var_abs2meta[abs_name]
        if prom_name not in memorize:
            if abs_name in mandatory_unconnected:
                mandatory_unconnected_vars.append(
                    Variable(prom_name, meta.get('value'), meta.get('units', None)))
            else:
                optional_unconnected_vars.append(
                    Variable(prom_name, meta.get('value'), meta.get('units', None)))
            memorize.append(prom_name)

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