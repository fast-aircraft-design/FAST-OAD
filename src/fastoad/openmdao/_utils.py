"""
Utility functions for OpenMDAO classes/instances
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
from typing import List, Tuple, TypeVar

import numpy as np
import openmdao.api as om
from deprecated import deprecated
from openmdao.core.constants import _SetupStatus
from openmdao.utils.mpi import FakeComm

T = TypeVar("T", bound=om.Problem)


def get_mpi_safe_problem_copy(problem: T) -> T:
    """
    This function does a deep copy of input OpenMDAO problem while avoiding
    the crash that can occur if problem.comm is not pickle-able, like a
    mpi4py.MPI.Intracomm object.

    :param problem:
    :return: a copy of the problem with a FakeComm object as problem.comm
    """
    with copyable_problem(problem) as no_mpi_problem:
        problem_copy = deepcopy(no_mpi_problem)

    return problem_copy


@contextmanager
def copyable_problem(problem: om.Problem) -> om.Problem:
    """
    Context manager that temporarily makes the input problem compatible with deepcopy.

    It ensures the problem gets back its original attributes after
    the `with` block is ended.

    :param problem: any openMDAO problem
    :return: The given problem with a FakeComm object as problem.comm
    """

    # An actual MPI communicator will make the deepcopy crash if an MPI
    # library is installed.
    actual_comm = problem.comm
    problem.comm = FakeComm()

    try:
        # Adding this attribute ensures that the post-hook for N2 reports
        # will not crash. Indeed, due to the copy, it tries to post-process
        # the 'problem' instance at the end of setup of the 'problem_copy' instance.
        if problem._metadata is None:
            problem._metadata = {}
        problem._metadata.update({"saved_errors": [], "setup_status": _SetupStatus.PRE_SETUP})

        yield problem
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
