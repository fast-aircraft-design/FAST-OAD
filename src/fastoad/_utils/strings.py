"""
Module for string-related operations
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

import io
import re

import numpy as np

from fastoad.exceptions import FastError


def get_float_list_from_string(text: str):
    """
    Parses the provided string and returns a list of floats if possible.

    If provided text is not numeric, None is returned.

    New line characters are simply ignored.

    As an example, following patterns will result as list [1., 2., 3.]

    .. code-block::

        '[ 1, 2., 3]'
        ' 1, 2., 3'
        ' 1 2  3'
        ' 1 2  3 dummy 4'
    """

    text_value = text.strip()
    if not text_value:
        return None

    # If it begins by '[', an array is expected, potentially multidimensional
    if text_value.startswith("["):
        # The string is first transformed in a way that can be parsed by genfromtxt
        text_value = re.sub(r"\r?\n|\r", "", text_value)  # first remove all new lines
        text_value = re.sub(r"\]\s*,\s*\[", "\n", text_value)
        text_value = text_value.strip("[]")
        text_io = io.StringIO(text_value)
        try:
            return np.genfromtxt(text_io, delimiter=",").tolist()
        except ValueError as exc:
            raise FastCouldNotParseStringToArrayError(text.strip(), exc)

    # Deals with multiple values in same element. numpy.fromstring can parse a string,
    # but we have to test with either ' ' or ',' as separator. The longest result should be
    # the good one.
    try:
        value1 = np.fromstring(text_value, dtype=float, sep=" ").tolist()
    except ValueError:
        pass

    try:
        value2 = np.fromstring(text_value, dtype=float, sep=",").tolist()
    except ValueError:
        pass

    if not value1 and not value2:
        return None

    return value1 if len(value1) > len(value2) else value2


class FastCouldNotParseStringToArrayError(FastError):
    """Raised when a conversion from string to array failed."""

    def __init__(self, parsed_text, original_exception):
        super().__init__()
        self.text = parsed_text
        self.original_exception = original_exception

    def __str__(self):
        msg = 'Could not parse "%s"' % self.text
        if self.original_exception:
            msg += ': got Error "%s"' % self.original_exception
        return msg
