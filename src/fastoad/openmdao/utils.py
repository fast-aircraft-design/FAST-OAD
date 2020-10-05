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
import openmdao.api as om


def get_unconnected_input_names(
    problem: om.Problem, promoted_names=False, logger: Logger = None
) -> Tuple[List[str], List[str]]:
    """
    For provided OpenMDAO problem, looks for inputs that are connected to no output.

    Inputs that have numpy.nan as default value are considered as mandatory. Other ones are
    considered as optional.

    If a logger is provided, it will issue errors for the first category, and warnings for the
    second one.

    :param problem: OpenMDAO Problem or System instance to inspect
    :param logger: optional logger instance
    :param promoted_names: if True, promoted names will be returned instead of absolute ones
    :return: tuple(list of missing mandatory inputs, list of missing optional inputs)
    """

    # Setup() is needed
    model = get_problem_after_setup(problem).model

    mandatory_unconnected = set()
    optional_unconnected = set()

    for abs_name, metadata in model.get_io_metadata(
        "input", metadata_keys=["value"], return_rel_names=False
    ).items():
        name = metadata["prom_name"] if promoted_names else abs_name
        if model.get_source(abs_name).startswith("_auto_ivc."):
            if np.all(np.isnan(metadata["value"])):
                mandatory_unconnected.add(name)
            else:
                optional_unconnected.add(name)

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
                value = model.get_io_metadata(metadata_keys=["value"])[abs_name]["value"]
                logger.warning("    %s : %s", abs_name, value)

    return list(mandatory_unconnected), list(optional_unconnected)


def get_problem_after_setup(problem: om.Problem) -> om.Problem:
    """
    This method should be used when an operation is needed that requires setup() to be run, without
    having the problem being actually setup.

    :param problem:
    :return: the problem itself if setup() has already been run, or a copy of the provided problem
             after setup() has been run
    """

    from openmdao.core.constants import _SetupStatus

    problem_is_setup = (
        problem._metadata and problem._metadata["setup_status"] >= _SetupStatus.POST_SETUP
    )

    if not problem_is_setup:
        # If setup() has not been done, we create a copy of the problem so we can work
        # on the model without doing setup() out of user notice
        tmp_problem = deepcopy(problem)
        tmp_problem.setup()
        return tmp_problem
    else:
        return problem
