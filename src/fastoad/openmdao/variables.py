"""
Module for managing OpenMDAO variables
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

import logging
import os.path as pth
import typing
from collections import OrderedDict
from typing import Dict, MutableMapping, Iterator, Hashable, AbstractSet, Union, Iterable

import numpy as np
import openmdao.api as om

# Logger for this module

_LOGGER = logging.getLogger(__name__)

RESOURCE_PATH = pth.join(pth.dirname(__file__), 'resources')
DESCRIPTION_FILE_PATH = pth.join(RESOURCE_PATH, 'variable_descriptions.txt')


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

    These keys can be listed with class method :meth:`get_authorized_keys`.
    **Any other key in kwargs will be silently ignored.**

    Special behaviour: :meth:`description` will return the content of kwargs['desc']
    unless these 2 conditions are met:
     - kwargs['desc'] is None or 'desc' key is missing
     - a description exists in FAST-OAD internal data for the variable name
    Then, the internal description will be returned by :meth:`description`

    :param kwargs: the attributes of the variable, as keyword arguments
    """

    # Will store content of DESCRIPTION_FILE_PATH once and for all
    _variable_descriptions = {}

    # Default metadata
    _base_metadata = {}

    def __init__(self, name, **kwargs: Dict):
        super().__init__()

        self.name = name
        """ Name of the variable """

        self.metadata: Dict = {}
        """ Dictionary for metadata of the variable """

        # Initialize class attributes once at first instantiation -------------
        if not self._variable_descriptions:
            # Class attribute, but it's safer to initialize it at first instantiation
            vars_descs = np.genfromtxt(DESCRIPTION_FILE_PATH, delimiter='\t', dtype=str)
            self.__class__._variable_descriptions.update(vars_descs)

        if not self._base_metadata:
            # Get variable base metadata from an IndepVarComp
            ivc = om.IndepVarComp()
            ivc.add_output(name='a')
            # get attributes (3rd element of the tuple) of first element
            self._base_metadata = ivc._indep_external[0][2]
            self._base_metadata['value'] = 1.0
        # Done with class attributes ------------------------------------------

        self.metadata = self._base_metadata.copy()
        # use kwargs only for keys already existent in self.metadata
        self.metadata.update((key, kwargs[key]) for key in kwargs.keys() & self.metadata.keys())
        self._set_default_shape()

        # If no description, add one from DESCRIPTION_FILE_PATH, if available
        if not self.description and self.name in self._variable_descriptions:
            self.description = self._variable_descriptions[self.name]

    @classmethod
    def get_authorized_keys(cls):
        """

        :return: the authorized keys when creating a Variable instance
        """
        return cls._base_metadata.keys()

    @property
    def value(self):
        """ value of the variable"""
        return self.metadata.get('value')

    @value.setter
    def value(self, value):
        self.metadata['value'] = value
        self._set_default_shape()

    @property
    def units(self):
        """ units associated to value (or None if not found) """
        return self.metadata.get('units')

    @units.setter
    def units(self, value):
        self.metadata['units'] = value

    @property
    def description(self):
        """ description of the variable (or None if not found) """
        return self.metadata.get('desc')

    @description.setter
    def description(self, value):
        self.metadata['desc'] = value

    def _set_default_shape(self):
        """ Automatically sets shape if not set"""
        if self.metadata['shape'] is None:
            shape = np.shape(self.value)
            if not shape:
                shape = (1,)
            self.metadata['shape'] = shape

    def __eq__(self, other):
        # same arrays with nan are declared non equals, so we need a workaround
        my_metadata = dict(self.metadata)
        other_metadata = dict(other.metadata)
        my_value = np.asarray(my_metadata.pop('value'))
        other_value = np.asarray(other_metadata.pop('value'))

        return (
                isinstance(other, Variable) and
                self.name == other.name and
                ((my_value == other_value) | (np.isnan(my_value) & np.isnan(other_value))).all() and
                my_metadata == other_metadata)

    def __repr__(self):
        return 'Variable(name=%s, metadata=%s)' % (self.name, self.metadata)

    def __hash__(self) -> int:
        return hash('var=' + self.name)  # Name is normally unique


class VariableList(MutableMapping):
    """
    Class for storing OpenMDAO variables

    Like a list of Variable instances, but items are accessed through variable names instead of
    indices.

    There are 2 ways for adding a variable::

        # Assuming these Python variables are ready
        var_1 = Variable('var/1', value=0.)
        metadata_2 = {'value': 1., 'units': 'm'}

        # ... a VariableList instance can be populated like this
        vars = VariableList()
        vars.append(var_1)              # Adds directly a Variable instance
        vars['var/2'] = metadata_2      # Adds the variable with given name and given metadata
        vars['var/1bis'] = var_1        # Adds the metadata of the Variable instance, associated to
                                        # provided name.

    After that, following equalities are True::

        print( var_1 in vars )
        print( 'var/1' in vars.names() )
        print( 'var/2' in vars.names() )
    """

    def __init__(self, iterable: Iterable[Variable] = None):
        super().__init__()
        self._variables: typing.OrderedDict[str, Variable] = OrderedDict()

        if iterable:
            for var in iterable:
                self.append(var)

    def append(self, variable: Variable):
        """
        Adds the provided Variable instance. The variable name will be its associated key.

        :param variable:
        """
        self._variables[variable.name] = variable

    def __setitem__(self, name: str, item: Union[Variable, dict]):
        if isinstance(item, Variable):
            if item.name != name:
                _LOGGER.warning(
                    'Variable List: Storing Variable "%s" using name "%s". '
                    'Initial name of variable will be lost.',
                    item.name, name)
                var = Variable(name, **item.metadata)
            else:
                var = item
        else:
            var = Variable(name, **item)

        self.append(var)

    def __delitem__(self, name: str) -> None:
        del self._variables[name]

    def __getitem__(self, name: str) -> Variable:
        return self._variables[name]

    def __len__(self) -> int:
        return len(self._variables)

    def __iter__(self) -> Iterator[Variable]:
        for var in self._variables.values():
            yield var

    def __contains__(self, var: Variable):
        return var in self._variables.values()

    def __eq__(self, other):
        # Need to be overloaded because the iterator returns values of the dict
        # BTW, we make that variable order does not matter
        return set(self) == set(other)

    def __repr__(self):
        return '\n'.join(map(str, self))

    def keys(self) -> AbstractSet[str]:
        # Need to be overloaded because the iterator returns values of the dict
        return self._variables.keys()

    def names(self) -> AbstractSet[str]:
        """
        Same as :meth:`keys`, but with a more appropriate name
        """
        return self.keys()
