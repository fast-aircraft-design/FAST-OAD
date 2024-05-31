"""
Class for managing an OpenMDAO variable.
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

import logging
from importlib.resources import open_text
from os import PathLike
from typing import Dict, Hashable, Iterable, Mapping, Tuple, Union

import numpy as np
import openmdao.api as om

from fastoad._utils.files import as_path
from fastoad._utils.resource_management.contents import PackageReader

_LOGGER = logging.getLogger(__name__)  # Logger for this module

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
    def read_variable_descriptions(
        cls, file_parent: Union[str, PathLike], update_existing: bool = True
    ):
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
        file_parent = as_path(file_parent)

        if not update_existing:
            cls._variable_descriptions = {}
            cls._loaded_descriptions = set()

        variable_descriptions = None
        description_file = None

        if file_parent:
            if file_parent.is_dir():
                file_path = file_parent / DESCRIPTION_FILENAME
                if file_path.is_file():
                    description_file = open(file_path)
            else:
                # Then it is a module name
                if DESCRIPTION_FILENAME in PackageReader(str(file_parent)).contents:
                    description_file = open_text(str(file_parent), DESCRIPTION_FILENAME)

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

    def get_openmdao_kwargs(self, keys: Iterable = None) -> dict:
        """
        Provides a dict usable as keyword args by OpenMDAO add_input()/add_output().

        The dict keys will be the ones provided, or a default set if no keys are provided.

        :param keys:
        :return: the kwargs dict
        """
        if not keys:
            keys = {
                "name",
                "val",
                "units",
                "desc",
            }
            if self.metadata["shape_by_conn"] or self.metadata["copy_shape"]:
                keys.add("shape_by_conn")
                keys.add("copy_shape")
            else:
                keys.add("shape")

        kwargs = {key: self.metadata[key] for key in self.get_openmdao_keys() if key in keys}
        kwargs["name"] = self.name
        return kwargs

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
            and (
                np.all(my_value == other_value)  # This condition is for val of type string
                or np.all(np.isclose(my_value, other_value, equal_nan=True))
            )
            and my_metadata == other_metadata
        )

    def __repr__(self):
        return "Variable(name=%s, metadata=%s)" % (self.name, self.metadata)

    def __hash__(self) -> int:
        return hash("var=" + self.name)  # Name is normally unique
