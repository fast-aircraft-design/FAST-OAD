# -*- coding: utf-8 -*-
"""
    Simple implementation of International Standard Atmosphere
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

from numbers import Number
from typing import Union, Sequence

import numpy as np
from scipy.constants import foot

GAS_CONSTANT = 287
SEA_LEVEL_PRESSURE = 101325
SEA_LEVEL_TEMPERATURE = 288.15
STRATOSPHERE_START = 11000


class Atmosphere:

    def __init__(self, altitude_ft: Union[float, Sequence[float]], delta_t: float = 0.):
        """
        Builds an atmosphere instance that will provide atmosphere values in the same shape as provided *altitude_ft*

        :param altitude_ft: altitude in foots
        :param delta_t: temperature increment applied to whole temperature profile
        """

        self.__delta_t = delta_t

        # Floats will be provided as output if altitude is a scalar
        self.__float_expected = isinstance(altitude_ft, Number)

        # For convenience, let's have altitude as numpy arrays in all cases
        if not isinstance(altitude_ft, np.ndarray):
            self.__altitude = np.array(altitude_ft) * foot
        else:
            self.__altitude = altitude_ft * foot

        self.__out_shape = self.__altitude.shape

        # Sets indices for tropopause
        self.__idx_tropo = self.__altitude < STRATOSPHERE_START
        self.__idx_strato = self.__altitude >= STRATOSPHERE_START

        # Outputs
        self.__temperature = None
        self.__pressure = None
        self.__density = None
        self.__speed_of_sound = None
        self.__kinematic_viscosity = None

    @property
    def temperature(self):
        if self.__temperature is None:
            self.__temperature = np.zeros(self.__out_shape)
            self.__temperature[self.__idx_tropo] = SEA_LEVEL_TEMPERATURE - 0.0065 * self.__altitude[
                self.__idx_tropo] + self.__delta_t
            self.__temperature[self.__idx_strato] = 216.65 + self.__delta_t
        return self.__return_value(self.__temperature)

    @property
    def pressure(self):
        if self.__pressure is None:
            self.__pressure = np.zeros(self.__out_shape)
            self.__pressure[self.__idx_tropo] = \
                SEA_LEVEL_PRESSURE * (1 - (self.__altitude[self.__idx_tropo] / 44330.78)) ** 5.25587611
            self.__pressure[self.__idx_strato] = \
                22632 * 2.718281 ** (1.7345725 - 0.0001576883 * self.__altitude[self.__idx_strato])
        return self.__return_value(self.__pressure)

    @property
    def density(self):
        if self.__density is None:
            self.__density = self.pressure / GAS_CONSTANT / self.temperature
        return self.__return_value(self.__density)

    @property
    def speed_of_sound(self):
        if self.__speed_of_sound is None:
            self.__speed_of_sound = (1.4 * GAS_CONSTANT * self.temperature) ** 0.5
        return self.__return_value(self.__speed_of_sound)

    @property
    def kinematic_viscosity(self):
        if self.__kinematic_viscosity is None:
            self.__kinematic_viscosity = ((0.000017894 * (self.temperature / SEA_LEVEL_TEMPERATURE) ** (3 / 2)) * (
                    (SEA_LEVEL_TEMPERATURE + 110.4) / (self.temperature + 110.4))) / self.density
        return self.__return_value(self.__kinematic_viscosity)

    def __return_value(self, value):
        """returns a float when needed"""
        if self.__float_expected:
            return float(value)
        else:
            return value
