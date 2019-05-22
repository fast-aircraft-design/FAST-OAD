# -*- coding: utf-8 -*-
"""
    Simple atmosphere function
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
from typing import Tuple

from scipy.constants import foot


# Simply derived from legacy version
# TODO : returning 5 values in a row is not so convenient. Should be
#  refactored a bit.
def atmosphere(altitude_ft: float, delta_t: float = 0.) \
        -> Tuple[float, float, float, float, float]:
    """
    Standard atmosphere data computation from given parameters.

    :param altitude_ft: altitude in feet
    :param delta_t: temperature offset in Kelvin degrees
    :return: tuple containing temperature in Kelvin degrees
    , density in kg/m3
    , pressure in kg/(m.s2) or Pa
    , kinematic viscosity in m2/s
    , speed of sound in m/s.
    """
    altitude_m = altitude_ft * foot
    if altitude_m <= 11000:
        temperature = (288.15 - 0.0065 * altitude_m) + delta_t
        pressure = 101325 * (1 - (altitude_m / 44330.78)) ** 5.25587611
    else:
        temperature = 216.65 + delta_t
        pressure = 22632 * 2.718281 ** (1.7345725 - 0.0001576883 * altitude_m)

    density = pressure / 287 / temperature
    viscosity = ((0.000017894 * (temperature / 288.15) ** (3 / 2))
                 * ((288.15 + 110.4) / (temperature + 110.4))) / density
    sos = (1.4 * 287 * temperature) ** 0.5

    return temperature, density, pressure, viscosity, sos
