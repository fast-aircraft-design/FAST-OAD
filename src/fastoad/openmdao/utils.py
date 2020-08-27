"""
Utility functions for OpenMDAO classes/instances
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
import openmdao
import openmdao.api as om
from packaging import version


# pylint: disable=protected-access #  needed for OpenMDAO introspection
def get_unconnected_input_names(
    problem: om.Problem, logger: Logger = None
) -> Tuple[List[str], List[str]]:
    """
    For provided OpenMDAO problem, looks for inputs that are connected to no output.

    Inputs that have numpy.nan as default value are considered as mandatory. Other ones are
    considered as optional.

    If a logger is provided, it will issue errors for the first category, and warnings for the
    second one.

    :param problem: OpenMDAO Problem or System instance to inspect
    :param logger: optional logger instance
    :return: tuple(list of missing mandatory inputs, list of missing optional inputs)
    """

    # Setup() is needed
    model = get_problem_after_setup(problem).model

    prom2abs: dict = model._var_allprocs_prom2abs_list["input"]
    connections: dict = model._conn_global_abs_in2out

    unconnected = set()

    if version.parse(openmdao.__version__) >= version.parse("3.2"):
        for abs_name, src in connections.items():
            if src.startswith("_auto_ivc."):
                unconnected.add(abs_name)
    else:
        for abs_names in prom2abs.values():
            # At each iteration, get absolute names that match one promoted name, or one
            # absolute name that has not been promoted.
            unconnected |= {
                a for a in abs_names if a not in connections or len(connections[a]) == 0
            }

    mandatory_unconnected = {
        abs_name
        for abs_name in unconnected
        if np.all(np.isnan(model._var_abs2meta[abs_name]["value"]))
    }
    optional_unconnected = unconnected - mandatory_unconnected

    if logger:
        if mandatory_unconnected:
            logger.error("Following inputs are required and not connected:")
            for abs_name in sorted(mandatory_unconnected):
                logger.error("    %s", abs_name)

        if optional_unconnected:
            logger.warning(
                "Following inputs are not connected so their default value will be used:"
            )
            for abs_name in sorted(optional_unconnected):
                value = model._var_abs2meta[abs_name]["value"]
                logger.warning("    %s : %s", abs_name, value)

    return list(mandatory_unconnected), list(optional_unconnected)


def get_problem_after_setup(problem: om.Problem) -> om.Problem:
    """
    This method should be used when an operation is needed that requires setup() to be run, without
    having the problem being actually setup.

    :param problem:
    :return: the problem itself it setup() has already been run, or a copy of the provided problem after setup()
             has been run
    """

    if problem._setup_status == 0:
        # If setup() has not been done, we create a copy of the problem so we can work
        # on the model without doing setup() out of user notice
        tmp_problem = deepcopy(problem)
        tmp_problem.setup()
        return tmp_problem
    else:
        return problem
