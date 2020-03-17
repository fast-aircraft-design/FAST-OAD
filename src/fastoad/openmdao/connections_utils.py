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
from copy import deepcopy
from logging import Logger
from typing import Tuple, List

import numpy as np
import pandas as pd
import openmdao.api as om

from fastoad.exceptions import NoSetupError
# pylint: disable=protected-access #  needed for OpenMDAO introspection
from fastoad.openmdao.variables import Variable, VariableList


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


def get_df_from_variables(variables: VariableList) -> pd.DataFrame:
    """
    Creates a DataFrame instance from a VariableList instance

    :param variables: a VariableList instance
    :return: a DataFrame instance
    """
    df = pd.DataFrame()
    col_names = ['Name', 'Value', 'Unit', 'Description']

    for variable in variables:
        attributes = variable.metadata.copy()
        df = df.append([{
            'Name': variable.name,
            'Value': variable.value,
            'Unit': attributes['units'],
            'Description': attributes['desc']
        }
        ])[col_names]

    return df


def get_variables_from_df(df: pd.DataFrame) -> VariableList:
    """
    Creates a VariableList instance from a DataFrame instance

    :param df: a DataFrame instance
    :return: a VariableList instance
    """
    variables = VariableList()

    for i, row in df.iterrows():
        name = row['Name']
        metadata = {'value': row['Value']}
        metadata.update({'units': row['Unit']})
        metadata.update({'desc': row['Description']})
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
        # If setup() has not been done, we create a copy of the problem so we can work
        # on the model without doing setup() out of user notice
        tmp_problem = deepcopy(problem)
        tmp_problem.setup()
        problem = tmp_problem

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
        # If setup() has not been done, we create a copy of the problem so we can work
        # on the model without doing setup() out of user notice
        tmp_problem = deepcopy(problem)
        tmp_problem.setup()
        problem = tmp_problem

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
