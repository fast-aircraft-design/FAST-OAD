"""
Utilities for mission computation.
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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
from scipy.constants import foot

FLIGHT_LEVEL = 100 * foot


def get_closest_flight_level(altitude, base_level=0, level_step=10, up_direction=True):
    """
    Computes the altitude (in meters) of a flight level close to provided altitude.

    Flight levels are multiples of 100 feet.

    see examples below::

        >>> # Getting the IFR flight level immediately above
        >>> get_closest_flight_level(4400. * foot)
        5000.0
        >>> # Getting the IFR flight level immediately below
        >>> get_closest_flight_level(4400. * foot, up_direction=False)
        4000.0
        >>> # Getting the next even IFR flight level
        >>> get_closest_flight_level(4400. * foot, level_step = 20)
        6000.0
        >>> # Getting the next odd IFR flight level
        >>> get_closest_flight_level(3100. * foot, base_level=10, level_step = 20)
        5000.0

    :param altitude: in meters
    :param base_level: base flight level for computed steps
    :param level_step: number of flight level per step
    :param up_direction: True if next flight level is upper. False if lower
    :return: the altitude in meters of the asked flight level.
    """
    if up_direction:
        func = np.ceil
    else:
        func = np.floor

    base_altitude = FLIGHT_LEVEL * base_level
    return base_altitude + FLIGHT_LEVEL * level_step * func(
        (altitude - base_altitude) / FLIGHT_LEVEL / level_step
    )
