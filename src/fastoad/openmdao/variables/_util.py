"""Utilities for VariableList."""
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

import itertools
from typing import Tuple

import numpy as np
from openmdao.core.constants import _SetupStatus

from fastoad.openmdao._utils import get_mpi_safe_problem_copy


def get_problem_variables(
    problem,
    get_promoted_names: bool = True,
    promoted_only: bool = True,
) -> Tuple[dict, dict]:
    """
    Creates dict instances (var_name vs metadata) containing inputs and outputs of an OpenMDAO
    Problem.

    The inputs (is_input=True) correspond to the variables of IndepVarComp
    components and all the unconnected input variables.

    .. note::

        Variables from _auto_ivc are ignored.

    :param problem: OpenMDAO Problem instance to inspect
    :param get_promoted_names: if True, promoted names will be returned instead of absolute ones
                               (if no promotion, absolute name will be returned)
    :param promoted_only: if True, only promoted variable names will be returned
    :return: input dict, output dict
    """
    if not problem._metadata or problem._metadata["setup_status"] < _SetupStatus.POST_SETUP:
        problem = get_mpi_safe_problem_copy(problem)
        problem.setup()

    # Get inputs and outputs
    metadata_keys = (
        "val",
        "units",
        "shape",
        "size",
        "desc",
        "ref",
        "ref0",
        "lower",
        "upper",
        "tags",
    )
    inputs = problem.model.get_io_metadata("input", metadata_keys=metadata_keys)
    outputs = problem.model.get_io_metadata(
        "output", metadata_keys=metadata_keys, excludes="_auto_ivc.*"
    )
    indep_outputs = problem.model.get_io_metadata(
        "output",
        metadata_keys=metadata_keys,
        tags=["indep_var", "openmdao:indep_var"],
        excludes="_auto_ivc.*",
    )
    # Move outputs from IndepVarComps into inputs
    for abs_name, metadata in indep_outputs.items():
        del outputs[abs_name]
        inputs[abs_name] = metadata

    # Remove non-promoted variables if needed
    if promoted_only:
        _remove_non_promoted(inputs)
        _remove_non_promoted(outputs)

        if get_promoted_names:
            # Check connections
            for name, metadata in inputs.copy().items():
                source_name = problem.model.get_source(name)
                if not (source_name.startswith("_auto_ivc.")) and source_name != name:
                    # This variable is connected to another variable of the problem: it is
                    # not an actual problem input. Let's move it to outputs.
                    del inputs[name]
                    outputs[name] = metadata

    # Add "is_input" field
    for metadata in inputs.values():
        metadata["is_input"] = True
    for metadata in outputs.values():
        metadata["is_input"] = False

    # Manage variable promotion
    if not get_promoted_names:
        final_inputs = inputs
        final_outputs = outputs
    else:
        final_inputs, final_outputs = _get_promoted_names(inputs, outputs)

    return final_inputs, final_outputs


def _remove_non_promoted(var_dict: dict):
    new_dict = {
        name: metadata for name, metadata in var_dict.items() if "." not in metadata["prom_name"]
    }
    var_dict.clear()
    var_dict.update(new_dict)


def _get_promoted_names(inputs, outputs):
    final_inputs = {
        metadata["prom_name"]: dict(metadata, is_input=True) for metadata in inputs.values()
    }
    final_outputs = _get_promoted_outputs(outputs)

    # Remove possible duplicates due to Indeps
    for input_name in final_inputs:
        if input_name in final_outputs:
            del final_outputs[input_name]

    # When variables are promoted, we may have retained a definition of the variable
    # that does not have any description, whereas a description is available in
    # another related definition (issue #319).
    # Therefore, we iterate again through original variable definitions to find
    # possible descriptions.
    for metadata in itertools.chain(inputs.values(), outputs.values()):
        prom_name = metadata["prom_name"]
        if not metadata["desc"]:
            continue
        for final in final_inputs, final_outputs:
            if prom_name in final and not final[prom_name]["desc"]:
                final[prom_name]["desc"] = metadata["desc"]
    return final_inputs, final_outputs


def _get_promoted_outputs(outputs: dict) -> dict:
    """

    :param outputs: dict (name, metadata) with non-promoted names as keys
    :return: dict (name, metadata) with promoted names as keys
    """
    promoted_outputs = {}
    for metadata in outputs.values():
        prom_name = metadata["prom_name"]
        # In case we get promoted names, several variables can match the same
        # promoted name, with possibly different declaration for default values.
        # We retain the first non-NaN value with defined units. If no units is
        # ever defined, the first non-NaN value is kept.
        # A non-NaN value with no units will be retained against a NaN value with
        # defined units.

        if prom_name in promoted_outputs:
            # prom_name has already been encountered.
            # Note: the succession of "if" is to help understanding, hopefully :)

            if not np.all(np.isnan(promoted_outputs[prom_name]["val"])):
                if promoted_outputs[prom_name]["units"] is not None:
                    # We already have a non-NaN value with defined units for current
                    # promoted name. No need for using the current variable.
                    continue
                if np.all(np.isnan(metadata["val"])):
                    # We already have a non-NaN value and current variable has a NaN value,
                    # so it can only add information about units. We keep the non-NaN value
                    continue

            if np.all(np.isnan(promoted_outputs[prom_name]["val"])) and metadata["units"] is None:
                # We already have a non-NaN value and current variable provides no unit.
                # No need for using the current variable.
                continue
        promoted_outputs[prom_name] = metadata

    return promoted_outputs
