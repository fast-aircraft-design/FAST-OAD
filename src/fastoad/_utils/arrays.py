"""
Module for array-related operations
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

from typing import Any

import numpy as np


def scalarize(value: Any):
    """
    :param value:
    :return: the scalar value inside input array if it is a one-element array/sequence.
             Returns `value` itself otherwise
    """
    try:
        return np.asarray(value).item()
    except ValueError:
        return value
