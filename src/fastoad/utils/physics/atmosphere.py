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

from numbers import Number
from typing import Union, Sequence

import numpy as np
from scipy.constants import foot, atmosphere, R

AIR_MOLAR_MASS = 28.9647e-3
AIR_GAS_CONSTANT = R / AIR_MOLAR_MASS
SEA_LEVEL_PRESSURE = atmosphere
SEA_LEVEL_TEMPERATURE = 288.15
TROPOPAUSE = 11000


class Atmosphere:
    """
    Simple implementation of International Standard Atmosphere
    for troposphere and stratosphere.

    Atmosphere properties a provided in the same "shape" as provided
    altitude:
     - if altitude is given as a float, returned values will be floats
     - if altitude is given as a sequence (list, 1D numpy array, ...), returned
       values will be 1D numpy arrays
     - if altitude is given as nD numpy array, returned values will be nD numpy
       arrays

    Usage:

    .. code-block::

        >>> pressure = Atmosphere(30000).pressure # pressure at 30,000 feet, dISA = 0 K
        >>> density = Atmosphere(5000, 10).density # density at 5,000 feet, dISA = 10 K


        >>> atm = Atmosphere(np.arange(0,10001,1000, 15)) # init for alt. 0 to 10,000, dISA = 15K
        >>> temperatures = atm.pressure # pressures for all defined altitudes
        >>> viscosities = atm.kinematic_viscosity # viscosities for all defined altitudes

    """

    # pylint: disable=too-many-instance-attributes  # Needed for avoiding redoing computations
    def __init__(self, altitude_ft: Union[float, Sequence[float]], delta_t: float = 0.):
        """
        Builds an atmosphere instance that will provide atmosphere values

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
        self.__idx_tropo = self.__altitude < TROPOPAUSE
        self.__idx_strato = self.__altitude >= TROPOPAUSE

        # Outputs
        self.__temperature = None
        self.__pressure = None
        self.__density = None
        self.__speed_of_sound = None
        self.__kinematic_viscosity = None

    @property
    def temperature(self):
        """ Temperature in K """
        if self.__temperature is None:
            self.__temperature = np.zeros(self.__out_shape)
            self.__temperature[self.__idx_tropo] = SEA_LEVEL_TEMPERATURE - 0.0065 \
                                                   * self.__altitude[self.__idx_tropo] \
                                                   + self.__delta_t
            self.__temperature[self.__idx_strato] = 216.65 + self.__delta_t
        return self.__return_value(self.__temperature)

    @property
    def pressure(self):
        """ Pressure in Pa """
        if self.__pressure is None:
            self.__pressure = np.zeros(self.__out_shape)
            self.__pressure[self.__idx_tropo] = \
                SEA_LEVEL_PRESSURE * (1 -
                                      (self.__altitude[self.__idx_tropo] / 44330.78)) ** 5.25587611
            self.__pressure[self.__idx_strato] = \
                22632 * 2.718281 ** (1.7345725 - 0.0001576883 * self.__altitude[self.__idx_strato])
        return self.__return_value(self.__pressure)

    @property
    def density(self):
        """ Density in kg/m3 """
        if self.__density is None:
            self.__density = self.pressure / AIR_GAS_CONSTANT / self.temperature
        return self.__return_value(self.__density)

    @property
    def speed_of_sound(self):
        """ Speed of sound in m/s """
        if self.__speed_of_sound is None:
            self.__speed_of_sound = (1.4 * AIR_GAS_CONSTANT * self.temperature) ** 0.5
        return self.__return_value(self.__speed_of_sound)

    @property
    def kinematic_viscosity(self):
        """ Kinematic viscosity in m2/s """
        if self.__kinematic_viscosity is None:
            self.__kinematic_viscosity = ((0.000017894 *
                                           (self.temperature / SEA_LEVEL_TEMPERATURE) ** (3 / 2))
                                          * ((SEA_LEVEL_TEMPERATURE + 110.4) /
                                             (self.temperature + 110.4))
                                          ) / self.density
        return self.__return_value(self.__kinematic_viscosity)

    def __return_value(self, value):
        """
        :returns: a float when needed. Otherwise, returns the value itself.
        """
        if self.__float_expected:
            return float(value)

        return value
