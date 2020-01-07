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

from logging import Logger
from typing import Tuple, List

import numpy as np
import openmdao.api as om

from fastoad.exceptions import NoSetupError
# pylint: disable=protected-access #  needed for OpenMDAO introspection
from fastoad.openmdao.variables import Variable


# TODO: separate the construction of Variable list from the creation of IndepVarComp
# TODO: factorize more code

def get_unconnected_inputs(problem: om.Problem,
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
    ivc = om.IndepVarComp()
    if problem._setup_status == 0:
        problem.setup()
    mandatory_unconnected, optional_unconnected = get_unconnected_inputs(problem)
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
                variable = Variable(name=prom_name,
                                    **metadata)  # useful because it adds a description if needed
                ivc.add_output(prom_name,
                               val=variable.value,
                               units=variable.units,
                               desc=variable.description)

    _add_outputs(mandatory_unconnected)
    if with_optional_inputs:
        _add_outputs(optional_unconnected)

    return ivc


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
    ivc = om.IndepVarComp()
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
        variable = Variable(name=prom_name,
                            **metadata)  # useful because it adds a description if needed
        if not initial_values:
            try:
                # Maybe useless, but we force units to ensure it is consistent
                variable.value = problem.get_val(prom_name, units=metadata['units'])
            except RuntimeError:
                # In case problem is incompletely set, problem.get_val() will fail.
                # In such case, falling back to the method for initial values
                # should be enough.
                pass
        ivc.add_output(prom_name,
                       val=variable.value,
                       units=variable.units,
                       desc=variable.description)

    return ivc


def update_ivc(original_ivc: om.IndepVarComp, reference_ivc: om.IndepVarComp) -> om.IndepVarComp:
    """
    Updates the values of an IndepVarComp instance with respect to a reference IndepVarComp
    instance

    :param original_ivc: IndepVarComp instance to be updated
    :param reference_ivc: IndepVarComp instance containing the default values for update
    :return updated_ivc: resulting IndepVarComp instance of the update
    """

    reference_variables = {}
    for (name, value, attributes) in reference_ivc._indep_external:
        reference_variables[name] = (value, attributes)

    updated_ivc = om.IndepVarComp()
    for (name, value, attributes) in original_ivc._indep_external:
        if name in reference_variables:
            value = reference_variables[name][0]
            attributes = reference_variables[name][1]
        updated_ivc.add_output(name, value, **attributes)

    return updated_ivc
