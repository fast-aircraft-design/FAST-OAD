"""
Exceptions for package configuration
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


from fastoad.exceptions import FastError


class FASTConfigurationBaseKeyBuildingError(FastError):
    """
    Class for being raised from bottom to top of TOML dict so that in the end, the message
    provides the full qualified name of the problematic key.

    using `new_err = FASTConfigurationBaseKeyBuildingError(err, 'new_err_key', <value>)`:

    - if err is a FASTConfigurationBaseKeyBuildingError instance with err.key=='err_key':
        - new_err.key will be 'new_err_key.err_key'
        - new_err.value will be err.value (no need to provide a value here)
        - new_err.original_exception will be err.original_exception
    - otherwise, new_err.key will be 'new_err_key' and new_err.value will be <value>
        - new_err.key will be 'new_err_key'
        - new_err.value will be <value>
        - new_err.original_exception will be err

    :param original_exception: the error that happened for raising this one
    :param key: the current key
    :param value: the current value
    """

    def __init__(self, original_exception: Exception, key: str, value=None):
        """Constructor"""

        self.key = None
        """
        the "qualified key" (like "problem.group.component1") related to error, build
        through raising up the error
        """

        self.value = None
        """ the value related to error """

        self.original_exception = None
        """ the original error, when eval failed """

        if hasattr(original_exception, "key"):
            self.key = "%s.%s" % (key, original_exception.key)
        else:
            self.key = key
        if hasattr(original_exception, "value"):
            self.value = "%s.%s" % (value, original_exception.value)
        else:
            self.value = value
        if hasattr(original_exception, "original_exception"):
            self.original_exception = original_exception.original_exception
        else:
            self.original_exception = original_exception
        super().__init__(
            self,
            'Attribute or value not recognized : %s = "%s"\nOriginal error: %s'
            % (self.key, self.value, self.original_exception),
        )


class FASTConfigurationBadOpenMDAOInstructionError(FASTConfigurationBaseKeyBuildingError):
    """Class for managing errors that result from trying to set an attribute by eval."""
