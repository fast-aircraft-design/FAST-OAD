"""
Module for managing OpenMDAO variables
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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

import os.path as pth
from collections import OrderedDict
from typing import Dict

import numpy as np

RESOURCE_PATH = pth.join(pth.dirname(__file__), 'resources')
DESCRIPTION_FILE_PATH = pth.join(RESOURCE_PATH, 'variable_descriptions.txt')


class Variables(OrderedDict):
    # Will store content of DESCRIPTION_FILE_PATH once and for all
    _variable_descriptions = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attributes: Dict = {}
        """
        Dictionary for all attributes of the variable
        """

        if not self._variable_descriptions:
            # Class attribute, but it's safer to initialize it at first instantiation
            vars_descs = np.genfromtxt(DESCRIPTION_FILE_PATH, delimiter='\t', dtype=str)
            self.__class__._variable_descriptions = {name: description for name, description in vars_descs}

    def __setitem__(self, key: str, attributes: dict):
        # If no description, add one from DESCRIPTION_FILE_PATH, if available
        if not attributes.get('desc') and key in self._variable_descriptions:
            attributes['desc'] = self._variable_descriptions[key]
        super().__setitem__(key, attributes)


class Variable:
    """
    A class for storing data of OpenMDAO variables.

    Instantiation is expected to be done through keyword arguments only.

    kwargs is expected to have keys 'name', 'value', 'units' and 'desc', that are
    accessible respectively through properties :meth:`name`, :meth:`value`,
    :meth:`units` and :meth:`description`.

    Special behaviour: :meth:`description` will return the content of kwargs['desc']
    unless these 2 conditions are met:
     - kwargs['desc'] is None or 'desc' key is missing
     - a description exists in FAST-OAD internal data for the variable name
    Then, the internal description will be returned by :meth:`description`

    :param kwargs: the attributes of the variable, as keyword arguments
    """

    # Will store content of DESCRIPTION_FILE_PATH once and for all
    _variable_descriptions = {}

    def __init__(self, **kwargs: Dict):
        self.attributes: Dict = {}
        """
        Dictionary for all attributes of the variable
        """

        if not self._variable_descriptions:
            # Class attribute, but it's safer to initialize it at first instantiation
            vars_descs = np.genfromtxt(DESCRIPTION_FILE_PATH, delimiter='\t', dtype=str)
            self.__class__._variable_descriptions = {name: description for name, description in
                                                     vars_descs}

        self.attributes.update(kwargs)

        # If no description, add one from DESCRIPTION_FILE_PATH, if available
        if not self.description and self.name in self._variable_descriptions:
            self.description = self._variable_descriptions[self.name]

    @property
    def name(self):
        """ name of the variable"""
        return self.attributes.get('name')

    @name.setter
    def name(self, value):
        self.attributes['name'] = value

    @property
    def value(self):
        """ value of the variable"""
        return self.attributes.get('value')

    @value.setter
    def value(self, value):
        self.attributes['value'] = value

    @property
    def units(self):
        """ units associated to value (or None if not found) """
        return self.attributes.get('units')

    @units.setter
    def units(self, value):
        self.attributes['units'] = value

    @property
    def description(self):
        """ description of the variable (or None if not found) """
        return self.attributes.get('desc')

    @description.setter
    def description(self, value):
        self.attributes['desc'] = value

    def __eq__(self, other):
        return (self.name == other.name and
                self.value == other.value and
                self.attributes == other.attributes)

    def __repr__(self):
        return 'Variable(name=%s, value=%s, units=%s)' % (self.name, self.value, self.units)
