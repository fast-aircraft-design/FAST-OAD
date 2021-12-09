"""
Module for managing OpenMDAO variables
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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
import logging
import os.path as pth
from builtins import isinstance
from copy import deepcopy
from importlib.resources import contents, open_text
from typing import Dict, Hashable, Iterable, List, Mapping, Tuple, Union

import numpy as np
import openmdao.api as om
import pandas as pd

from ._utils import get_unconnected_input_names

# Logger for this module
_LOGGER = logging.getLogger(__name__)

DESCRIPTION_FILENAME = "variable_descriptions.txt"

# Metadata that will be ignore when checking variable equality and when adding variable
# to an OpenMDAO component
METADATA_TO_IGNORE = [
    "is_input",
    "tags",
    "size",
    "src_indices",
    "src_slice",
    "flat_src_indices",
    "distributed",
    "res_units",  # deprecated in IndepVarComp.add_output() since OpenMDAO 3.2
    "lower",  # deprecated in IndepVarComp.add_output() since OpenMDAO 3.2
    "upper",  # deprecated in IndepVarComp.add_output() since OpenMDAO 3.2
    "ref",  # deprecated in IndepVarComp.add_output() since OpenMDAO 3.2
    "ref0",  # deprecated in IndepVarComp.add_output() since OpenMDAO 3.2
    "res_ref",  # deprecated in IndepVarComp.add_output() since OpenMDAO 3.2
    "ref",  # deprecated in IndepVarComp.add_output() since OpenMDAO 3.2
    "global_shape",
    "global_size",
    "discrete",  # currently inconsistent in openMDAO 3.4
    "prom_name",
    "desc",
]


class Variable(Hashable):
    """
    A class for storing data of OpenMDAO variables.

    Instantiation is expected to be done through keyword arguments only.

    Beside the mandatory parameter 'name, kwargs is expected to have keys
    'value', 'units' and 'desc', that are accessible respectively through
    properties :meth:`name`, :meth:`value`, :meth:`units` and :meth:`description`.

    Other keys are possible. They match the definition of OpenMDAO's method
    :meth:`Component.add_output` described
    `here <http://openmdao.org/twodocs/versions/latest/_srcdocs/packages/core/
    component.html#openmdao.core.component.Component.add_output>`_.

    These keys can be listed with class method :meth:`get_openmdao_keys`.
    **Any other key in kwargs will be silently ignored.**

    Special behaviour: :meth:`description` will return the content of kwargs['desc']
    unless these 2 conditions are met:
     - kwargs['desc'] is None or 'desc' key is missing
     - a description exists in FAST-OAD internal data for the variable name
    Then, the internal description will be returned by :meth:`description`

    :param kwargs: the attributes of the variable, as keyword arguments
    """

    # Will store content of description files
    _variable_descriptions = {}

    # The list of modules of path where description files have been read
    _loaded_descriptions = set()

    # Default metadata
    _base_metadata = {}

    def __init__(self, name, **kwargs):
        super().__init__()

        self.name = name
        """ Name of the variable """

        self.metadata: Dict = {}
        """ Dictionary for metadata of the variable """

        # Initialize class attributes once at first instantiation -------------
        if not self._base_metadata:
            # Get variable base metadata from an ExplicitComponent
            comp = om.ExplicitComponent()
            # get attributes
            metadata = comp.add_output(name="a")

            self.__class__._base_metadata = metadata
            self.__class__._base_metadata["val"] = 1.0
            self.__class__._base_metadata["tags"] = set()
            self.__class__._base_metadata["shape"] = None
        # Done with class attributes ------------------------------------------

        # Feed self.metadata with kwargs, but remove first attributes with "Unavailable" as
        # value, which is a value that can be provided by OpenMDAO.
        self.metadata = self.__class__._base_metadata.copy()
        self.metadata.update(
            {
                key: value
                for key, value in kwargs.items()
                # The isinstance check is needed if value is a numpy array. In this case, a
                # FutureWarning is issued because it is compared to a scalar.
                if not isinstance(value, str) or value != "Unavailable"
            }
        )

        if "value" in self.metadata:
            self.metadata["val"] = self.metadata.pop("value")
        if "description" in self.metadata:
            self.metadata["desc"] = self.metadata.pop("description")

        self._set_default_shape()

        # If no description, use the one from self._variable_descriptions, if available
        if not self.description and self.name in self._variable_descriptions:
            self.description = self._variable_descriptions[self.name]

    @classmethod
    def read_variable_descriptions(cls, file_parent: str, update_existing: bool = True):
        """
        Reads variable descriptions in indicated folder or package, if it contains some.

        The file variable_descriptions.txt is looked for. Nothing is done if it is not
        found (no error raised also).

        Each line of the file should be formatted like::

            my:variable||The description of my:variable, as long as needed, but on one line.

        :param file_parent: the folder path or the package name that should contain the file
        :param update_existing: if True, previous descriptions will be updated.
                                if False, previous descriptions will be erased.
        """
        if not update_existing:
            cls._variable_descriptions = {}
            cls._loaded_descriptions = set()

        variable_descriptions = None
        description_file = None

        if file_parent:
            if pth.isdir(file_parent):
                file_path = pth.join(file_parent, DESCRIPTION_FILENAME)
                if pth.isfile(file_path):
                    description_file = open(file_path)
            else:
                # Then it is a module name
                if DESCRIPTION_FILENAME in contents(file_parent):
                    description_file = open_text(file_parent, DESCRIPTION_FILENAME)

        if description_file is not None:
            try:
                variable_descriptions = np.genfromtxt(
                    description_file, delimiter="||", dtype=str, autostrip=True
                )
            except Exception as exc:
                # Reading the file is not mandatory, so let's just log the error.
                _LOGGER.error(
                    "Could not read file %s in %s. Error log is:\n%s",
                    DESCRIPTION_FILENAME,
                    file_parent,
                    exc,
                )
            description_file.close()

        if variable_descriptions is not None:
            if np.shape(variable_descriptions) == (2,):
                # If the file contains only one line, np.genfromtxt() will return a (2,)-shaped
                # array. We need a reshape for dict.update() to work correctly.
                variable_descriptions = np.reshape(variable_descriptions, (1, 2))

            cls._loaded_descriptions.add(file_parent)
            cls.update_variable_descriptions(variable_descriptions)
            _LOGGER.info("Loaded variable descriptions in %s", file_parent)

    @classmethod
    def update_variable_descriptions(
        cls, variable_descriptions: Union[Mapping[str, str], Iterable[Tuple[str, str]]]
    ):
        """
        Updates description of variables.

        :param variable_descriptions: dict-like object with variable names as keys and descriptions
                                      as values
        """
        cls._variable_descriptions.update(variable_descriptions)

    @classmethod
    def get_openmdao_keys(cls):
        """

        :return: the keys that are used in OpenMDAO variables
        """
        # As _base_metadata is initialized at first instantiation, we create an instance to
        # ensure it has been done
        cls("dummy")

        return cls._base_metadata.keys()

    @property
    def value(self):
        """value of the variable"""
        return self.metadata.get("val")

    @value.setter
    def value(self, value):
        self.metadata["val"] = value
        self._set_default_shape()

    @property
    def val(self):
        """value of the variable (alias of property "value")"""
        return self.value

    @val.setter
    def val(self, value):
        self.value = value

    @property
    def units(self):
        """units associated to value (or None if not found)"""
        return self.metadata.get("units")

    @units.setter
    def units(self, value):
        self.metadata["units"] = value

    @property
    def description(self):
        """description of the variable (or None if not found)"""
        return self.metadata.get("desc")

    @description.setter
    def description(self, value):
        self.metadata["desc"] = value

    @property
    def desc(self):
        """description of the variable (or None if not found) (alias of property "description")"""
        return self.description

    @desc.setter
    def desc(self, value):
        self.description = value

    @property
    def is_input(self):
        """I/O status of the variable.

        - True if variable is a problem input
        - False if it is an output
        - None if information not found
        """
        return self.metadata.get("is_input")

    @is_input.setter
    def is_input(self, value):
        self.metadata["is_input"] = value

    def _set_default_shape(self):
        """Automatically sets shape if not set"""
        if self.metadata["shape"] is None:
            shape = np.shape(self.value)
            if not shape:
                shape = (1,)
            self.metadata["shape"] = shape

    def __eq__(self, other):
        # same arrays with nan are declared non equals, so we need a workaround
        my_metadata = dict(self.metadata)
        other_metadata = dict(other.metadata)
        my_value = np.asarray(my_metadata.pop("val"))
        other_value = np.asarray(other_metadata.pop("val"))

        # Let's also ignore unimportant keys
        for key in METADATA_TO_IGNORE:
            if key in my_metadata:
                del my_metadata[key]
            if key in other_metadata:
                del other_metadata[key]

        return (
            isinstance(other, Variable)
            and self.name == other.name
            and np.all(np.isclose(my_value, other_value, equal_nan=True))
            and my_metadata == other_metadata
        )

    def __repr__(self):
        return "Variable(name=%s, metadata=%s)" % (self.name, self.metadata)

    def __hash__(self) -> int:
        return hash("var=" + self.name)  # Name is normally unique


class VariableList(list):
    """
    Class for storing OpenMDAO variables

    A list of Variable instances, but items can also be accessed through variable names.

    There are 2 ways for adding a variable::

        # Assuming these Python variables are ready
        var_1 = Variable('var/1', value=0.)
        metadata_2 = {'value': 1., 'units': 'm'}

        # ... a VariableList instance can be populated like this
        vars = VariableList()
        vars.append(var_1)              # Adds directly a Variable instance
        vars['var/2'] = metadata_2      # Adds the variable with given name and given metadata

    After that, following equalities are True::

        print( var_1 in vars )
        print( 'var/1' in vars.names() )
        print( 'var/2' in vars.names() )

    Note:
        Adding a Variable instance that has a name that is already in the VariableList instance
        will replace the previous Variable instance instead of adding a new one.
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

    def update(self, other_var_list: "VariableList", add_variables: bool = True):
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
                if var.name in self.names():
                    if self[var.name].description and not var.description:
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

        # To be able to edit floats and integer
        def _check_shape(value):
            if np.shape(value) == (1,):
                value = float(value[0])
            elif np.shape(value) == ():
                pass
            else:
                value = np.asarray(value).tolist()
            return value

        for variable in self:
            value = _check_shape(variable.value)
            var_dict["name"].append(variable.name)
            for metadata_name in self.metadata_keys():
                if metadata_name == "val":
                    var_dict["val"].append(value)
                else:
                    # TODO: make this more generic
                    if metadata_name in ["val", "initial_value", "lower", "upper"]:
                        metadata = _check_shape(variable.metadata[metadata_name])
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
        variables = VariableList()

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
        variables = VariableList()

        ivc = deepcopy(ivc)
        om.Problem(ivc).setup()  # Need setup to have get_io_metadata working

        for name, metadata in ivc.get_io_metadata(
            metadata_keys=["val", "units", "upper", "lower"]
        ).items():
            metadata = metadata.copy()
            value = metadata.pop("val")
            if np.shape(value) == (1,):
                value = float(value[0])
            elif np.shape(value) == ():
                pass
            else:
                value = np.asarray(value)
            metadata.update({"val": value})
            variables[name] = metadata

        return variables

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

        # To be able to edit floats and integer
        def _check_shape(value):
            if np.shape(value) == (1,):
                value = float(value[0])
            elif np.shape(value) == ():
                if type(value) == str:
                    value = float(value)
                else:
                    # Integer
                    pass
            else:
                value = np.asarray(value).tolist()
            return value

        def _get_variable(row):
            var_as_dict = {key: val for key, val in zip(column_names, row)}
            # TODO: make this more generic
            for key, val in var_as_dict.items():
                if key in ["val", "initial_value", "lower", "upper"]:
                    var_as_dict[key] = _check_shape(val)
                else:
                    pass
            return Variable(**var_as_dict)

        return VariableList([_get_variable(row) for row in df[column_names].values])

    @classmethod
    def from_problem(
        cls,
        problem: om.Problem,
        use_initial_values: bool = False,
        get_promoted_names: bool = True,
        promoted_only: bool = True,
    ) -> "VariableList":
        """
        Creates a VariableList instance containing inputs and outputs of an OpenMDAO Problem.

        .. warning::

            problem.setup() must have been run.

        The inputs (is_input=True) correspond to the variables of IndepVarComp
        components and all the unconnected variables.

        .. note::

            Variables from _auto_ivc are ignored.

        :param problem: OpenMDAO Problem instance to inspect
        :param use_initial_values: if True, returned instance will contain values before computation
        :param get_promoted_names: if True, promoted names will be returned instead of absolute ones
                                   (if no promotion, absolute name will be returned)
        :param promoted_only: if True, only promoted variable names will be returned
        :return: VariableList instance
        """

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
            "output", metadata_keys=metadata_keys, tags="indep_var", excludes="_auto_ivc.*"
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
                    if not source_name.startswith("_auto_ivc.") and source_name != name:
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
            # Remove from inputs the variables that are outputs of some other component
            promoted_inputs = {
                metadata["prom_name"]: dict(metadata, is_input=True) for metadata in inputs.values()
            }

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
                if prom_name not in promoted_inputs:
                    promoted_outputs[prom_name] = metadata

            final_inputs = promoted_inputs
            final_outputs = promoted_outputs

            # When variables are promoted, we may have retained a definition of the variable
            # that does not have any description, whereas a description is available in
            # another related definition (issue #319).
            # Therefore, we iterate again through original variable definitions to find
            # possible descriptions.
            for metadata in itertools.chain(inputs.values(), outputs.values()):
                prom_name = metadata["prom_name"]
                if metadata["desc"]:
                    for final in final_inputs, final_outputs:
                        if prom_name in final and not final[prom_name]["desc"]:
                            final[prom_name]["desc"] = metadata["desc"]

        # Conversion to VariableList instances
        input_vars = VariableList.from_dict(final_inputs)
        output_vars = VariableList.from_dict(final_outputs)

        # Use computed value instead of initial ones, if asked for
        for variable in input_vars + output_vars:
            if not use_initial_values:
                try:
                    # Maybe useless, but we force units to ensure it is consistent
                    variable.value = problem.get_val(variable.name, units=variable.units)
                except RuntimeError:
                    # In case problem is incompletely set, problem.get_val() will fail.
                    # In such case, falling back to the method for initial values
                    # should be enough.
                    pass

        return input_vars + output_vars

    @classmethod
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
