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

from typing import Union, Iterable

import numpy as np

from fastoad.exceptions import FastUnexpectedKeywordArgument


class DynamicAttributeDict(dict):
    def __init__(self, *args, **kwargs):
        """
        A dictionary class where keys can also be used as attributes.

        The keys that can be used as attributes are defined using decorators
        :class:`AddKeyAttribute` or  :class:`SetKeyAttributes`.

        They can also be used as keyword arguments when instantiating this class.

        .. Note::

            Using this class as a dict is useful when instantiating another
            dict or a pandas DataFrame, or instantiating from them. Direct interaction
            with DynamicAttributeDict instance should be done through attributes.

        Example::

            >>> @AddKeyAttributes({"foo": 0.0, "bar": None, "baz": 42.0})
            ... class MyDict(DynamicAttributeDict):
            ...     pass
            ...

            >>> d = MyDict(foo=5, bar="aa")
            >>> d.foo
            5
            >>> d.bar
            'aa'
            >>> d.baz  # returns the default value
            42.0
            >>> d["foo"] = 10.0  # can still be used as a dict
            >>> d.foo  # but change are propagated to/from the matching attribute
            10.0
            >>> d.foo = np.nan  # setting None or numpy.nan returns to default value
            >>> d["foo"]
            0.0
            >>> d.foo # But the attribute will now return the default value
            0.0
            >>> d.bar = None  # If default value is None, setting None or numpy.nan deletes the key.
            >>> # d["bar"]  #would trigger a key error
            >>> d.bar # But the attribute will return None

        :param args: a dict-like object where all keys are contained in :attr:`attribute_keys`
        :param kwargs: argument keywords must be names contained in :attr:`attribute_keys`
        """

        if hasattr(self, "get_attribute_keys"):
            for key in kwargs:
                if key not in self.get_attribute_keys():
                    raise FastUnexpectedKeywordArgument(key)
        elif kwargs:
            # No defined dynamic attribute, any keyword argument is illegal
            raise FastUnexpectedKeywordArgument(list(kwargs.keys())[0])

        super().__init__(*args, **kwargs)

        if hasattr(self, "get_attribute_keys"):
            # Keys with None or Nan as value will be deleted so their default value
            # will be returned (see property definition in AddKeyAttribute).
            # We apply this behaviour even when instantiating from *args (i.e. with
            # a dict-like object)
            for key in self.get_attribute_keys():
                if key in self and (self[key] is None or _is_nan(self[key])):
                    del self[key]


class AddKeyAttribute:
    def __init__(self, attr_name, default_value=None, doc=None):
        """
        A decorator for a dict class that adds a property for accessing the matching dict item.

        The getter and the setter of the property are defined.
        Setting None or np.nan when setting the property will delete the dict key, so that
        next calls to the getter will return default_value.

        Calling AddKeyAttribute for an already defined key will redefine the default value.

        The "attribute_keys" property is created in decorated class for returning the list
        of attributes that have been defined by AddKeyAttribute or by
        :class:`AddKeyAttributes`.

        :param attr_name: the dict key that will be paired to a property
        :param default_value: the default value that will be returned if dict has not
                              the attr_name as key
        """
        self.attr_name = attr_name
        self.default_value = default_value
        self.doc = doc

    def __call__(self, decorated_dict: type):
        # Adds the property for defined key
        def _getter(self_):
            return self_.get(self.attr_name, self.default_value)

        def _setter(self_, value):
            if self.attr_name in self_ and (value is None or _is_nan(value)):
                # None or NaN means the default value, so we delete the dict key
                if self.default_value is None:
                    del self_[self.attr_name]
                else:
                    self_[self.attr_name] = self.default_value
            else:
                self_[self.attr_name] = value

        prop = property(_getter, _setter, doc=self.doc)
        setattr(decorated_dict, self.attr_name, prop)

        # Adds the method for getting the list of keys paired to attributes
        try:
            decorated_dict._attribute_keys.add(self.attr_name)
        except AttributeError:
            decorated_dict._attribute_keys = {self.attr_name}

        def get_attribute_keys(cls):
            """:return: list of attributes paired to dict key."""
            return cls._attribute_keys

        decorated_dict.get_attribute_keys = classmethod(get_attribute_keys)

        return decorated_dict


class AddKeyAttributes:
    def __init__(self, attribute_definition: Union[dict, Iterable[str]]):
        """
        A decorator for a dict class that adds properties for accessing the matching dict item.

        This class simply does several call of :class:`AddKeyAttribute`.

        :param attribute_definition: the list of keys that will be attributes. If it is
                                     a dictionary, the values are the associated default values.
                                     If it is a list or a set, default values will be None.
        """
        if isinstance(attribute_definition, dict):
            self.attribute_definition = attribute_definition
        else:
            self.attribute_definition = {attr_name: None for attr_name in attribute_definition}

    def __call__(self, decorated_dict: type):

        for attr_name, definition in self.attribute_definition.items():
            if isinstance(definition, dict):
                default_value = definition.get("default")
                doc = definition.get("doc")
            else:
                default_value = definition
                doc = None
            decorated_dict = AddKeyAttribute(attr_name, default_value, doc)(decorated_dict)

        return decorated_dict


def _is_nan(value):
    """Tells if value is numpy.nan in a robust way."""
    try:
        return np.all(np.isnan(value))
    except TypeError:
        return False  # if there has been a type error, then it is not NaN
