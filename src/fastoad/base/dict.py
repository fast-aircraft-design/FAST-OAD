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

import numpy as np
from fastoad.exceptions import FastUnexpectedKeywordArgument


class DynamicAttributeDict(dict):
    def __init__(self, *args, **kwargs):
        """
        A dictionary class where keys are also used as attribute names.

        Each subclass can define its own attributes with their default values

        :param args: a dict-like object where all keys are contained in :attr:`labels`
        :param kwargs: must be name contained in :attr:`labels`
        """

        # Initialize defaults (in case no subclass did it)
        self._set_attribute_defaults({})

        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if key not in self._keyword_args:
                raise FastUnexpectedKeywordArgument(key)

        # Apply defaults for non-defined keys
        for key, value in self._keyword_args.items():
            if key in self and self[key] is None:
                # Setting the argument value to None is like not providing it.
                del self[key]

            if value and key not in self:
                # If an attribute as not be set, use default value if any
                self[key] = value

            # When going from DynamicAttributeDict to DataFrame, None values become NaN.
            # But in the other side, NaN values will stay NaN, so, if some fields are
            # not set, we would not have:
            # >>> flight_point == DynamicAttributeDict(pd.DataFrame([flight_point]).iloc[0])
            # So we remove NaN values to ensure the equality above in any case.
            try:
                if key in self and np.all(np.isnan(self[key])):
                    del self[key]
            except TypeError:
                pass  # if there has been a type error, then self[key] is not NaN

    def __getattribute__(self, name):
        if name == "_keyword_args":
            try:
                return super(DynamicAttributeDict, self).__getattribute__(name)
            except AttributeError:
                super(DynamicAttributeDict, self).__setattr__("_keyword_args", {})
                return super(DynamicAttributeDict, self).__getattribute__(name)
        else:
            if name in self._keyword_args:
                return self.get(name)
            else:
                return super(DynamicAttributeDict, self).__getattribute__(name)

    def __setattr__(self, name, value):
        if name not in self._keyword_args:
            super(DynamicAttributeDict, self).__setattr__(name, value)
        else:
            self[name] = value

    def _set_attribute_defaults(self, default_dict):
        """
        Sets defaults for keyword arguments at class instantiation.

        This method is intended for being used in __init__ of subclasses before
        calling the __init__ of the superclass.

        Set None as default value for authorizing the keyword argument without
        setting a default value.

        Important note: if a default value has been already set, it won't be
        overwritten. This way, the definition in last subclass will prevail.

        :param default_dict: a dict with attribute names and their default value.
        """
        for attr_name, default_value in default_dict.items():
            if attr_name not in self._keyword_args:
                self._keyword_args[attr_name] = default_value
