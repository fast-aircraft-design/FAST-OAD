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

from collections import Sequence
from typing import Union

import numpy as np
from fastoad.exceptions import FastUnexpectedKeywordArgument


class DynamicAttributeDict(dict):
    def __init__(self, *args, **kwargs):
        """
        A dictionary class where keys can also be used as attributes.

        The keys that can be used as attributes are defined using decorators
        :class:`DynamicAttributeDictDecorator` or  :class:`DynamicAttributesDictDecorator`.

        They can also be used as keyword arguments when instantiating this class.

        :param args: a dict-like object where all keys are contained in :attr:`attribute_keys`
        :param kwargs: must be name contained in :attr:`attribute_keys`
        """

        if hasattr(self, "attribute_keys"):
            for key in kwargs:
                if key not in self.attribute_keys:
                    raise FastUnexpectedKeywordArgument(key)
        elif kwargs:
            # No defined dynamic attribute, any keyword argument is illegal
            raise FastUnexpectedKeywordArgument(list(kwargs.keys())[0])

        super().__init__(*args, **kwargs)

        if hasattr(self, "attribute_keys"):
            # Keys with None or Nan as value will be deleted so their default value
            # will be returned (see property definition in DynamicAttributeDictDecorator).
            # We apply this behaviour even when instantiating from *args (i.e. with
            # a dict-like object)
            for key in self.attribute_keys:
                if key in self and (self[key] is None or _is_nan(self[key])):
                    del self[key]


class DynamicAttributeDictDecorator:
    def __init__(self, attr_name, default_value):
        """
        A decorator for a dict class that adds a property for accessing the matching dict item.

        The getter and the setter of the property are defined.
        Setting None or np.nan when setting the property will delete the dict key, so that
        next calls to the getter will return default_value.

        The "attribute_keys" property is created in decorated class for returning the list
        of attributes that have been defined by DynamicAttributeDictDecorator or by
        :class:`DynamicAttributesDictDecorator`.

        :param attr_name: the dict key that will be paired to a property
        :param default_value: the default value that will be returned if dict has not
                              the attr_name as key
        """
        self.attr_name = attr_name
        self.default_value = default_value

    def __call__(self, decorated_dict: type):
        # Adds the property for defined key
        def _getter(self_):
            """The property getter"""
            return self_.get(self.attr_name, self.default_value)

        def _setter(self_, value):
            """The property setter"""
            if self.attr_name in self_ and (value is None or _is_nan(value)):
                # None or NaN means the default value, so we delete the dict key
                del self_[self.attr_name]
            else:
                self_[self.attr_name] = value

        prop = property(_getter, _setter)
        setattr(decorated_dict, self.attr_name, prop)

        # Adds the property for getting the list of keys paired to attributes
        try:
            decorated_dict._attribute_keys.append(self.attr_name)
        except AttributeError:
            decorated_dict._attribute_keys = [self.attr_name]

        decorated_dict.attribute_keys = property(lambda self_: self_.__class__._attribute_keys)

        return decorated_dict


class DynamicAttributesDictDecorator:
    def __init__(self, attribute_definition: Union[dict, Sequence]):
        """
        A decorator for a dict class that adds properties for accessing the matching dict item.

        This class simply does several call of :class:`DynamicAttributeDictDecorator`.

        :param attribute_definition: the list of keys that will be attributes. If it is
                                     a dictionary, the values are the associated default values.
                                     If it is a sequence, default values will be None.
        """
        if isinstance(attribute_definition, dict):
            self.attribute_definition = attribute_definition
        else:
            self.attribute_definition = {attr_name: None for attr_name in attribute_definition}

    def __call__(self, decorated_dict: type):

        for attr_name, default_value in self.attribute_definition.items():
            decorated_dict = DynamicAttributeDictDecorator(attr_name, default_value)(decorated_dict)

        return decorated_dict


def _is_nan(value):
    """Tells if value is numpy.nan in a robust way."""
    try:
        return np.all(np.isnan(value))
    except TypeError:
        return False  # if there has been a type error, then it is not NaN
