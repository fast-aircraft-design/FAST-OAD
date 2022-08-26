"""
Class for managing a list of OpenMDAO variables.
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

import itertools
from copy import deepcopy
from typing import Iterable, List, Mapping, Tuple, Union

import numpy as np
import openmdao.api as om
import pandas as pd
from deprecated import deprecated
from openmdao.core.constants import _SetupStatus

from fastoad.openmdao._utils import get_unconnected_input_names, problem_without_mpi
from .variable import METADATA_TO_IGNORE, Variable


class VariableList(list):
    """
    Class for storing OpenMDAO variables.

    A list of :class:`~fastoad.openmdao.variables.variable.Variable` instances, but items can
    also be accessed through variable names. It also has utilities to be converted from/to some
    other data structures (python dict, OpenMDAO IndepVarComp, pandas DataFrame)

    See documentation of :class:`~fastoad.openmdao.variables.variable.Variable` to see how to
    manipulate each element.

    There are several ways for adding variables::

        # Assuming these Python variables are ready...
        var_1 = Variable('var/1', value=0.)
        metadata_2 = {'value': 1., 'units': 'm'}

        # ... a VariableList instance can be populated like this:
        vars_A = VariableList()
        vars_A.append(var_1)              # Adds directly a Variable instance
        vars_A['var/2'] = metadata_2      # Adds the variable with given name and given metadata

    Note:
        Adding a Variable instance with a name that is already in the VariableList instance
        will replace the previous Variable instance instead of adding a new one.

    .. code:: python

        # It is also possible to instantiate a VariableList instance from another VariableList
        # instance or a simple list of Variable instances
        vars_B = VariableList(vars_A)
        vars_C = VariableList([var_1])

        # An existing VariableList instance can also receive the content of another VariableList
        # instance.
        vars_C.update(vars_A)             # variables in vars_A will overwrite variables with same
                                          # name in vars_C

    After that, following equalities are True::

        print( var_1 in vars_A )
        print( 'var/1' in vars_A.names() )
        print( 'var/2' in vars_A.names() )
    """

    def names(self) -> List[str]:
        """
        :return: names of variables
        """
        return [var.name for var in self]

    def metadata_keys(self) -> List[str]:
        """
        :return: the metadata keys that are common to all variables in the list
        """
        keys = list(self[0].metadata.keys())
        for var in self:
            keys = [key for key in var.metadata.keys() if key in keys]
        return keys

    def append(self, var: Variable) -> None:
        """
        Append var to the end of the list, unless its name is already used. In that case, var
        will replace the previous Variable instance with the same name.
        """
        if not isinstance(var, Variable):
            raise TypeError("VariableList items should be Variable instances")

        if var.name in self.names():
            self[self.names().index(var.name)] = var
        else:
            super().append(var)

    def update(self, other_var_list: list, add_variables: bool = True):
        """
        Uses variables in other_var_list to update the current VariableList instance.

        For each Variable instance in other_var_list:
            - if a Variable instance with same name exists, it is replaced by the one
              in other_var_list (special case: if one in other_var_list has an empty description,
              the original description is kept)
            - if not, Variable instance from other_var_list will be added only if
              add_variables==True

        :param other_var_list: source for new Variable data
        :param add_variables: if True, unknown variables are also added
        """

        for var in other_var_list:
            if add_variables or var.name in self.names():
                # To avoid to lose variables description when the variable list is updated with a
                # list without descriptions (issue # 319)
                if var.name in self.names() and self[var.name].description and not var.description:
                    var.description = self[var.name].description
                self.append(deepcopy(var))

    def to_ivc(self) -> om.IndepVarComp:
        """
        :return: an OpenMDAO IndepVarComp instance with all variables from current list
        """
        ivc = om.IndepVarComp()
        for variable in self:
            attributes = variable.metadata.copy()
            value = attributes.pop("val")
            # Some attributes are not compatible with add_output
            for attr in METADATA_TO_IGNORE:
                if attr in attributes:
                    del attributes[attr]
            ivc.add_output(variable.name, value, **attributes)

        return ivc

    def to_dataframe(self) -> pd.DataFrame:
        """
        Creates a DataFrame instance from a VariableList instance.

        Column names are "name" + the keys returned by :meth:`Variable.get_openmdao_keys`.
        Values in Series "value" are floats or lists (numpy arrays are converted).

        :return: a pandas DataFrame instance with all variables from current list
        """
        var_dict = {"name": []}
        var_dict.update({metadata_name: [] for metadata_name in self.metadata_keys()})

        for variable in self:
            value = self._as_list_or_float(variable.value)
            var_dict["name"].append(variable.name)
            for metadata_name in self.metadata_keys():
                if metadata_name == "val":
                    var_dict["val"].append(value)
                else:
                    # TODO: make this more generic
                    if metadata_name in ["val", "initial_value", "lower", "upper"]:
                        metadata = self._as_list_or_float(variable.metadata[metadata_name])
                    else:
                        metadata = variable.metadata[metadata_name]
                    var_dict[metadata_name].append(metadata)

        df = pd.DataFrame.from_dict(var_dict)

        return df

    @classmethod
    def from_dict(
        cls, var_dict: Union[Mapping[str, dict], Iterable[Tuple[str, dict]]]
    ) -> "VariableList":
        """
        Creates a VariableList instance from a dict-like object.

        :param var_dict:
        :return: a VariableList instance
        """
        variables = cls()

        for var_name, metadata in dict(var_dict).items():
            variables.append(Variable(var_name, **metadata))

        return variables

    @classmethod
    def from_ivc(cls, ivc: om.IndepVarComp) -> "VariableList":
        """
        Creates a VariableList instance from an OpenMDAO IndepVarComp instance

        :param ivc: an IndepVarComp instance
        :return: a VariableList instance
        """
        variables = cls()

        ivc = deepcopy(ivc)
        om.Problem(ivc).setup()  # Need setup to have get_io_metadata working

        for name, metadata in ivc.get_io_metadata(
            metadata_keys=["val", "units", "upper", "lower"]
        ).items():
            metadata = metadata.copy()
            value = metadata.pop("val")
            value = cls._as_list_or_float(value)
            metadata.update({"val": value})
            variables[name] = metadata

        return variables

    @classmethod
    def _as_list_or_float(cls, value):
        value = np.asarray(value)
        if np.size(value) == 1:
            value = value.item()
            try:
                value = float(value)
            except (TypeError, ValueError):
                pass
            return value

        return value.tolist()

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "VariableList":
        """
        Creates a VariableList instance from a pandas DataFrame instance.

        The DataFrame instance is expected to have column names "name" + some keys among the ones
        given by :meth:`Variable.get_openmdao_keys`.

        :param df: a DataFrame instance
        :return: a VariableList instance
        """
        column_names = [name for name in df.columns]

        def _get_variable(row):
            var_as_dict = {key: val for key, val in zip(column_names, row)}
            # TODO: make this more generic
            for key, val in var_as_dict.items():
                if key in ["val", "initial_value", "lower", "upper"]:
                    var_as_dict[key] = cls._as_list_or_float(val)
                else:
                    pass
            return Variable(**var_as_dict)

        return cls([_get_variable(row) for row in df[column_names].values])

    @classmethod
    def from_problem(
        cls,
        problem: om.Problem,
        use_initial_values: bool = False,
        get_promoted_names: bool = True,
        promoted_only: bool = True,
        io_status: str = "all",
    ) -> "VariableList":
        """
        Creates a VariableList instance containing inputs and outputs of an OpenMDAO Problem.

        The inputs (is_input=True) correspond to the variables of IndepVarComp
        components and all the unconnected variables.

        .. note::

            Variables from _auto_ivc are ignored.

        :param problem: OpenMDAO Problem instance to inspect
        :param use_initial_values: if True, or if problem has not been run, returned instance will
                                   contain values before computation
        :param get_promoted_names: if True, promoted names will be returned instead of absolute ones
                                   (if no promotion, absolute name will be returned)
        :param promoted_only: if True, only promoted variable names will be returned
        :param io_status: to choose with type of variable we return ("all", "inputs, "outputs")
        :return: VariableList instance
        """

        if not problem._metadata or problem._metadata["setup_status"] < _SetupStatus.POST_SETUP:
            with problem_without_mpi(problem) as problem_copy:
                problem_copy.setup()
                problem = problem_copy

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
            "output", metadata_keys=metadata_keys, tags="indep_var"
        )
        # Move outputs from IndepVarComps into inputs
        for abs_name, metadata in indep_outputs.items():
            del outputs[abs_name]
            inputs[abs_name] = metadata

        # Remove non-promoted variables if needed
        if promoted_only:
            inputs = {
                name: metadata
                for name, metadata in inputs.items()
                if "." not in metadata["prom_name"]
            }
            outputs = {
                name: metadata
                for name, metadata in outputs.items()
                if "." not in metadata["prom_name"]
            }

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
            final_inputs = {
                metadata["prom_name"]: dict(metadata, is_input=True) for metadata in inputs.values()
            }
            final_outputs = cls._get_promoted_outputs(outputs)

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

        # Conversion to VariableList instances
        input_vars = cls.from_dict(final_inputs)
        output_vars = cls.from_dict(final_outputs)

        # Use computed value instead of initial ones, if asked for, and if problem has been run.
        # Note: using problem.get_val() if problem has not been run may lead to unexpected
        # behaviour when actually running the problem.
        if not use_initial_values and problem.model.iter_count > 0:
            for variable in input_vars + output_vars:
                try:
                    # Maybe useless, but we force units to ensure it is consistent
                    variable.value = problem.get_val(variable.name, units=variable.units)
                except RuntimeError:
                    # In case problem is incompletely set, problem.get_val() will fail.
                    # In such case, falling back to the method for initial values
                    # should be enough.
                    pass

        if io_status == "all":
            variables = input_vars + output_vars
        elif io_status == "inputs":
            variables = input_vars
        elif io_status == "outputs":
            variables = output_vars
        else:
            raise ValueError("Unknown value for io_status")

        return variables

    @classmethod
    def _get_promoted_outputs(cls, outputs: dict) -> dict:
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

                if (
                    np.all(np.isnan(promoted_outputs[prom_name]["val"]))
                    and metadata["units"] is None
                ):
                    # We already have a non-NaN value and current variable provides no unit.
                    # No need for using the current variable.
                    continue
            promoted_outputs[prom_name] = metadata

        return promoted_outputs

    @classmethod
    @deprecated(
        version="1.3.0",
        reason="Will be removed in version 2.0. Please use VariableList.from_problem() instead",
    )
    def from_unconnected_inputs(
        cls, problem: om.Problem, with_optional_inputs: bool = False
    ) -> "VariableList":
        """
        Creates a VariableList instance containing unconnected inputs of an OpenMDAO Problem.

        .. warning::

            problem.setup() must have been run.

        If *optional_inputs* is False, only inputs that have numpy.nan as default value (hence
        considered as mandatory) will be in returned instance. Otherwise, all unconnected inputs
        will be in returned instance.

        :param problem: OpenMDAO Problem instance to inspect
        :param with_optional_inputs: If True, returned instance will contain all unconnected inputs.
                                Otherwise, it will contain only mandatory ones.
        :return: VariableList instance
        """
        variables = VariableList()

        mandatory_unconnected, optional_unconnected = get_unconnected_input_names(problem)
        model = problem.model

        # processed_prom_names will store promoted names that have been already processed, so that
        # it won't be stored twice.
        # By processing mandatory variable first, a promoted variable that would be mandatory
        # somewhere and optional elsewhere will be retained as mandatory (and associated value
        # will be NaN), which is fine.
        # For promoted names that link to several optional variables and no mandatory ones,
        # associated value will be the first encountered one, and this is as good a choice as any
        # other.
        processed_prom_names = []

        io_metadata = model.get_io_metadata(
            metadata_keys=["val", "units", "desc"], return_rel_names=False
        )

        def _add_outputs(unconnected_names):
            """Fills ivc with data associated to each provided var"""
            for abs_name in unconnected_names:
                prom_name = io_metadata[abs_name]["prom_name"]
                if prom_name not in processed_prom_names:
                    processed_prom_names.append(prom_name)
                    metadata = deepcopy(io_metadata[abs_name])
                    metadata.update({"is_input": True})
                    variables[prom_name] = metadata
                elif not variables[prom_name].description and io_metadata[abs_name]["desc"]:
                    variables[prom_name].description = io_metadata[abs_name]["desc"]

        _add_outputs(mandatory_unconnected)
        if with_optional_inputs:
            _add_outputs(optional_unconnected)

        return variables

    def __getitem__(self, key) -> Variable:
        if isinstance(key, str):
            return self[self.names().index(key)]
        else:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        if isinstance(key, str):
            if isinstance(value, dict):
                variable = Variable(key, **value)
                if key in self.names():
                    self[key].metadata = variable.metadata
                else:
                    self.append(variable)
            else:
                raise TypeError(
                    'VariableList can be set with "vars[key] = value" only if value is a '
                    "dict of metadata"
                )
        elif not isinstance(value, Variable):
            raise TypeError("VariableList items should be Variable instances")
        else:
            super().__setitem__(key, value)

    def __delitem__(self, key):
        if isinstance(key, str):
            del self[self.names().index(key)]
        else:
            super().__delitem__(key)

    def __add__(self, other) -> Union[List, "VariableList"]:
        if isinstance(other, VariableList):
            return VariableList(super().__add__(other))
        else:
            return super().__add__(other)
