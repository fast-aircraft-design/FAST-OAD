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

import numpy as np


def get_float_list_from_string(text: str):
    """
    Parses the provided string and returns a list of floats if possible.

    If provided text is not numeric, None is returned.

    As an example, following patterns will result as list [1., 2., 3.]

    .. code-block::

        '[ 1, 2., 3]'
        '[ 1 2.  3]'
        ' 1, 2., 3'
        ' 1 2  3'
        ' 1 2  3 dummy 4'
    """

    text_value = text.strip().strip('[]')
    if not text_value:
        return None

    # Deals with multiple values in same element. numpy.fromstring can parse a string,
    # but we have to test with either ' ' or ',' as separator. The longest result should be
    # the good one.
    value1 = np.fromstring(text_value, dtype=float, sep=' ').tolist()
    value2 = np.fromstring(text_value, dtype=float, sep=',').tolist()

    if not value1 and not value2:
        return None

    return value1 if len(value1) > len(value2) else value2
