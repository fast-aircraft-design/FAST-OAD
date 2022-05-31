"""
Utility functions for OpenMDAO classes/instances
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

from contextlib import contextmanager
from copy import deepcopy
from typing import List, Tuple

import numpy as np
import openmdao.api as om
from deprecated import deprecated
from openmdao.utils.mpi import FakeComm


@contextmanager
def problem_without_mpi(problem: om.Problem) -> om.Problem:
    """
    Context manager that delivers a copy of the given OpenMDAO problem.

    A deepcopy operation may crash if problem.comm is not pickle-able, like a
    mpi4py.MPI.Intracomm object.

    This context manager temporarily sets a FakeComm object as problem.comm and
    does the copy.

    It ensures the original problem gets back its original communicator after
    the `with` block is ended.

    :param problem: any openMDAO problem
    :return: A copy of the given problem with a FakeComm object as problem.comm
    """
    # An actual MPI communicator will make the deepcopy crash if an MPI
    # library is installed.

    actual_comm = problem.comm
    problem.comm = FakeComm()

    try:
        problem_copy = deepcopy(problem)
        problem_copy.comm = problem.comm
        yield problem_copy
    finally:
        problem.comm = actual_comm


@deprecated(
    version="1.3.0",
    reason="Will be removed in version 2.0. Please use VariableList.from_problem() instead",
)
def get_unconnected_input_names(
    problem: om.Problem, promoted_names=False
) -> Tuple[List[str], List[str]]:
    """
    For provided OpenMDAO problem, looks for inputs that are connected to no output.

    .. warning::

        problem.setup() must have been run.

    Inputs that have numpy.nan as default value are considered as mandatory. Other ones are
    considered as optional.

    :param problem: OpenMDAO Problem or System instance to inspect
    :param promoted_names: if True, promoted names will be returned instead of absolute ones
    :return: tuple(list of missing mandatory inputs, list of missing optional inputs)
    """

    model = problem.model

    mandatory_unconnected = set()
    optional_unconnected = set()

    for abs_name, metadata in model.get_io_metadata(
        "input", metadata_keys=["val"], return_rel_names=False
    ).items():
        name = metadata["prom_name"] if promoted_names else abs_name
        if model.get_source(abs_name).startswith("_auto_ivc."):
            if np.all(np.isnan(metadata["val"])):
                mandatory_unconnected.add(name)
            else:
                optional_unconnected.add(name)

    # If a promoted variable is defined both with NaN and non-NaN value, it is
    # considered as mandatory
    if promoted_names:
        optional_unconnected = optional_unconnected - mandatory_unconnected

    return list(mandatory_unconnected), list(optional_unconnected)
