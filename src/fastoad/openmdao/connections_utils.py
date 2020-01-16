"""
Utility functions for OpenMDAO classes/instances
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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
import warnings
from logging import Logger
from typing import Tuple, List

import numpy as np
import openmdao.api as om

from fastoad.exceptions import NoSetupError
# pylint: disable=protected-access #  needed for OpenMDAO introspection
from fastoad.openmdao.variables import Variable, VariableList


# TODO: separate the construction of Variable list from the creation of IndepVarComp
# TODO: factorize more code

def get_ivc_from_variables(variables: VariableList) -> om.IndepVarComp:
    """
    Creates an IndepVarComp instance from a VariableList instance

    :param variables: a VariableList instance
    :return: an IndepVarComp instance
    """
    ivc = om.IndepVarComp()
    for variable in variables:
        attributes = variable.metadata.copy()
        value = attributes.pop('value')
        ivc.add_output(variable.name, value, **attributes)

    return ivc


def get_variables_from_ivc(ivc: om.IndepVarComp) -> VariableList:
    """
    Creates a VariableList instance from an IndepVarComp instance

    :param ivc: an IndepVarComp instance
    :return: a VariableList instance
    """
    variables = VariableList()

    for (name, value, attributes) in ivc._indep + ivc._indep_external:
        metadata = {'value': value}
        metadata.update(attributes)
        variables[name] = metadata

    return variables


def get_variables_from_problem(problem: om.Problem,
                               initial_values: bool = False,
                               use_inputs: bool = True,
                               use_outputs: bool = True) -> VariableList:
    """
    This function returns an VariableList instance containing
    variables (inputs and/or outputs) of a an OpenMDAO Problem.

    If variables are promoted, the promoted name will be used. Otherwise, the absolute name will be
    used.

    :param problem: OpenMDAO Problem instance to inspect
    :param initial_values: if True, returned instance will contain values before computation
    :param use_inputs: if True, returned instance will contain inputs of the problem
    :param use_outputs: if True, returned instance will contain outputs of the problem
    :return: VariableList instance
    """
    variables = VariableList()
    if problem._setup_status == 0:
        problem.setup()
    system = problem.model

    prom2abs = {}
    if use_inputs:
        prom2abs.update(system._var_allprocs_prom2abs_list['input'])
    if use_outputs:
        prom2abs.update(system._var_allprocs_prom2abs_list['output'])

    for prom_name, abs_names in prom2abs.items():
        # Pick the first
        abs_name = abs_names[0]
        metadata = system._var_abs2meta[abs_name]
        variable = Variable(name=prom_name, **metadata)
        if not initial_values:
            try:
                # Maybe useless, but we force units to ensure it is consistent
                variable.value = problem.get_val(prom_name, units=variable.units)
            except RuntimeError:
                # In case problem is incompletely set, problem.get_val() will fail.
                # In such case, falling back to the method for initial values
                # should be enough.
                pass
        variables.append(variable)

    return variables


def get_unconnected_input_variables(problem: om.Problem,
                                    with_optional_inputs: bool = False) -> VariableList:
    """
    This function returns an VariableList instance containing
    all the unconnected inputs of a Problem.

    If *optional_inputs* is False, only inputs that have numpy.nan as default value (hence
    considered as mandatory) will be in returned instance. Otherwise, all unconnected inputs will
    be in returned instance.

    :param problem: OpenMDAO Problem instance to inspect
    :param with_optional_inputs: If True, returned instance will contain all unconnected inputs.
                            Otherwise, it will contain only mandatory ones.
    :return: VariableList instance
    """
    variables = VariableList()

    if problem._setup_status == 0:
        problem.setup()
    mandatory_unconnected, optional_unconnected = get_unconnected_input_names(problem)
    model = problem.model

    # processed_prom_names will store promoted names that have been already processed, so that
    # it won't be stored twice.
    # By processing mandatory variable first, a promoted variable that would be mandatory somewhere
    # and optional elsewhere will be retained as mandatory (and associated value will be NaN),
    # which is fine.
    # For promoted names that link to several optional variables and no mandatory ones, associated
    # value will be the first encountered one, and this is as good a choice as any other.
    processed_prom_names = []

    def _add_outputs(unconnected_names):
        """ Fills ivc with data associated to each provided var"""
        for abs_name in unconnected_names:
            prom_name = model._var_abs2prom['input'][abs_name]
            if prom_name not in processed_prom_names:
                processed_prom_names.append(prom_name)
                metadata = model._var_abs2meta[abs_name]
                variables[prom_name] = metadata

    _add_outputs(mandatory_unconnected)
    if with_optional_inputs:
        _add_outputs(optional_unconnected)

    return variables


def get_unconnected_input_names(problem: om.Problem,
                                logger: Logger = None) -> Tuple[List[str], List[str]]:
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

    model = problem.model

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
                value = model._var_abs2meta[abs_name]['value']
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
                value = model._var_abs2meta[abs_name]['value']
                logger.warning('    %s : %s', abs_name, value)

    return mandatory_unconnected, optional_unconnected


def build_ivc_of_unconnected_inputs(problem: om.Problem,
                                    with_optional_inputs: bool = False) -> om.IndepVarComp:
    """
    This function returns an OpenMDAO IndepVarComp instance containing
    all the unconnected inputs of a Problem.

    If *optional_inputs* is False, only inputs that have numpy.nan as default value (hence
    considered as mandatory) will be in returned instance. Otherwise, all unconnected inputs will
    be in returned instance.

    :param problem: OpenMDAO Problem instance to inspect
    :param with_optional_inputs: If True, returned instance will contain all unconnected inputs.
                            Otherwise, it will contain only mandatory ones.
    :return: IndepVarComp instance
    """

    warnings.warn('Use get_unconnected_input_variables() and get_ivc_from_variables() instead',
                  DeprecationWarning)

    variables = get_unconnected_input_variables(problem, with_optional_inputs)
    return get_ivc_from_variables(variables)


def build_ivc_of_variables(problem: om.Problem,
                           initial_values: bool = False,
                           use_inputs: bool = True,
                           use_outputs: bool = True) -> om.IndepVarComp:
    """
    This function returns an OpenMDAO IndepVarComp instance containing
    variables (inputs and/or outputs) of a an OpenMDAO Problem.

    If variables are promoted, the promoted name will be used. Otherwise, the absolute name will be
    used.

    :param problem: OpenMDAO Problem instance to inspect
    :param initial_values: if True, returned instance will contain values before computation
    :param use_inputs: if True, returned instance will contain inputs of the problem
    :param use_outputs: if True, returned instance will contain outputs of the problem
    :return: IndepVarComp instance
    """

    warnings.warn('Use get_variables_from_problem() and get_ivc_from_variables() instead',
                  DeprecationWarning)

    variables = get_variables_from_problem(problem, initial_values, use_inputs, use_outputs)
    return get_ivc_from_variables(variables)


def update_ivc(original_ivc: om.IndepVarComp, reference_ivc: om.IndepVarComp) -> om.IndepVarComp:
    """
    Updates the values of an IndepVarComp instance with respect to a reference IndepVarComp
    instance

    :param original_ivc: IndepVarComp instance to be updated
    :param reference_ivc: IndepVarComp instance containing the default values for update
    :return updated_ivc: resulting IndepVarComp instance of the update
    """

    warnings.warn(
        'Use VariableList.update(), possibly with '
        'get_ivc_from_variables() and/or get_variables_from_ivc ',
        DeprecationWarning)

    variables = get_variables_from_ivc(original_ivc)
    ref_variables = get_variables_from_ivc(reference_ivc)

    variables.update(ref_variables)
    return get_ivc_from_variables(variables)

    # reference_variables = {}
    # for (name, value, attributes) in reference_ivc._indep_external:
    #     reference_variables[name] = (value, attributes)
    #
    # updated_ivc = om.IndepVarComp()
    # for (name, value, attributes) in original_ivc._indep_external:
    #     if name in reference_variables:
    #         value = reference_variables[name][0]
    #         attributes = reference_variables[name][1]
    #     updated_ivc.add_output(name, value, **attributes)
    #
    # return updated_ivc
