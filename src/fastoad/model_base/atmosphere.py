"""
Simple implementation of International Standard Atmosphere.
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

from numbers import Number
from typing import Sequence, Union

import numpy as np
from deprecated import deprecated
from scipy.constants import R, atmosphere, foot

AIR_MOLAR_MASS = 28.9647e-3
AIR_GAS_CONSTANT = R / AIR_MOLAR_MASS
SEA_LEVEL_PRESSURE = atmosphere
SEA_LEVEL_TEMPERATURE = 288.15
TROPOPAUSE = 11000


@deprecated(
    version="1.2.0", reason="Will be removed in version 2.0. Please use stdatm.Atmosphere instead"
)
class Atmosphere:
    """
    Simple implementation of International Standard Atmosphere
    for troposphere and stratosphere.

    Atmosphere properties are provided in the same "shape" as provided
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
    def __init__(
        self,
        altitude: Union[float, Sequence[float]],
        delta_t: float = 0.0,
        altitude_in_feet: bool = True,
    ):
        """
        :param altitude: altitude (units decided by altitude_in_feet)
        :param delta_t: temperature increment (°C) applied to whole temperature profile
        :param altitude_in_feet: if True, altitude should be provided in feet. Otherwise,
                                 it should be provided in meters.
        """
        self.delta_t = delta_t

        # Floats will be provided as output if altitude is a scalar
        self._float_expected = isinstance(altitude, Number)

        # For convenience, let's have altitude as numpy arrays and in meters in all cases
        unit_coeff = foot if altitude_in_feet else 1.0
        self._altitude = np.asarray(altitude) * unit_coeff

        # Sets indices for tropopause
        self._idx_tropo = self._altitude < TROPOPAUSE
        self._idx_strato = self._altitude >= TROPOPAUSE

        # Outputs
        self._temperature = None
        self._pressure = None
        self._density = None
        self._speed_of_sound = None
        self._kinematic_viscosity = None
        self._mach = None
        self._equivalent_airspeed = None
        self._true_airspeed = None
        self._unitary_reynolds = None

    def get_altitude(self, altitude_in_feet: bool = True) -> Union[float, Sequence[float]]:
        """
        :param altitude_in_feet: if True, altitude is returned in feet. Otherwise,
                                 it is returned in meters
        :return: altitude provided at instantiation
        """
        if altitude_in_feet:
            return self._return_value(self._altitude / foot)
        return self._return_value(self._altitude)

    @property
    def delta_t(self) -> Union[float, Sequence[float]]:
        """Temperature increment applied to whole temperature profile."""
        return self._delta_t

    @delta_t.setter
    def delta_t(self, value: Union[float, Sequence[float]]):
        self._delta_t = np.asarray(value)

    @property
    def temperature(self) -> Union[float, Sequence[float]]:
        """Temperature in K."""
        if self._temperature is None:
            self._temperature = np.zeros(self._altitude.shape)
            self._temperature[self._idx_tropo] = (
                SEA_LEVEL_TEMPERATURE - 0.0065 * self._altitude[self._idx_tropo] + self._delta_t
            )
            self._temperature[self._idx_strato] = 216.65 + self._delta_t
        return self._return_value(self._temperature)

    @property
    def pressure(self) -> Union[float, Sequence[float]]:
        """Pressure in Pa."""
        if self._pressure is None:
            self._pressure = np.zeros(self._altitude.shape)
            self._pressure[self._idx_tropo] = (
                SEA_LEVEL_PRESSURE
                * (1 - (self._altitude[self._idx_tropo] / 44330.78)) ** 5.25587611
            )
            self._pressure[self._idx_strato] = 22632 * 2.718281 ** (
                1.7345725 - 0.0001576883 * self._altitude[self._idx_strato]
            )
        return self._return_value(self._pressure)

    @property
    def density(self) -> Union[float, Sequence[float]]:
        """Density in kg/m3."""
        if self._density is None:
            self._density = self.pressure / AIR_GAS_CONSTANT / self.temperature
        return self._return_value(self._density)

    @property
    def speed_of_sound(self) -> Union[float, Sequence[float]]:
        """Speed of sound in m/s."""
        if self._speed_of_sound is None:
            self._speed_of_sound = (1.4 * AIR_GAS_CONSTANT * self.temperature) ** 0.5
        return self._return_value(self._speed_of_sound)

    @property
    def kinematic_viscosity(self) -> Union[float, Sequence[float]]:
        """Kinematic viscosity in m2/s."""
        if self._kinematic_viscosity is None:
            self._kinematic_viscosity = (
                (0.000017894 * (self.temperature / SEA_LEVEL_TEMPERATURE) ** (3 / 2))
                * ((SEA_LEVEL_TEMPERATURE + 110.4) / (self.temperature + 110.4))
            ) / self.density
        return self._return_value(self._kinematic_viscosity)

    @property
    def mach(self) -> Union[float, Sequence[float]]:
        """Mach number."""
        if self._mach is None and self.true_airspeed is not None:
            self._mach = self.true_airspeed / self.speed_of_sound
        return self._return_value(self._mach)

    @property
    def true_airspeed(self) -> Union[float, Sequence[float]]:
        """True airspeed (TAS) in m/s."""
        # Dev note: true_airspeed is the "hub". Other speed values will be calculated
        # from this true_airspeed.
        if self._true_airspeed is None:
            if self._mach is not None:
                self._true_airspeed = self._mach * self.speed_of_sound
            if self._equivalent_airspeed is not None:
                sea_level = Atmosphere(0)
                self._true_airspeed = self._equivalent_airspeed * np.sqrt(
                    sea_level.density / self.density
                )
            if self._unitary_reynolds is not None:
                self._true_airspeed = self._unitary_reynolds * self.kinematic_viscosity
        return self._return_value(self._true_airspeed)

    @property
    def equivalent_airspeed(self) -> Union[float, Sequence[float]]:
        """Equivalent airspeed (EAS) in m/s."""
        if self._equivalent_airspeed is None and self.true_airspeed is not None:
            sea_level = Atmosphere(0)
            self._equivalent_airspeed = self.true_airspeed / np.sqrt(
                sea_level.density / self.density
            )

        return self._return_value(self._equivalent_airspeed)

    @property
    def unitary_reynolds(self) -> Union[float, Sequence[float]]:
        """Unitary Reynolds number in 1/m."""
        if self._unitary_reynolds is None and self.true_airspeed is not None:
            self._unitary_reynolds = self.true_airspeed / self.kinematic_viscosity
        return self._return_value(self._unitary_reynolds)

    @mach.setter
    def mach(self, value: Union[float, Sequence[float]]):
        self._reset_speeds()
        self._mach = np.asarray(value)

    @true_airspeed.setter
    def true_airspeed(self, value: Union[float, Sequence[float]]):
        self._reset_speeds()
        self._true_airspeed = np.asarray(value)

    @equivalent_airspeed.setter
    def equivalent_airspeed(self, value: Union[float, Sequence[float]]):
        self._reset_speeds()
        self._equivalent_airspeed = np.asarray(value)

    @unitary_reynolds.setter
    def unitary_reynolds(self, value: Union[float, Sequence[float]]):
        self._reset_speeds()
        self._unitary_reynolds = np.asarray(value)

    def _reset_speeds(self):
        """To be used before setting a new speed value as private attribute."""
        self._mach = None
        self._true_airspeed = None
        self._equivalent_airspeed = None
        self._unitary_reynolds = None

    def _return_value(self, value):
        """
        :returns: a float when needed. Otherwise, returns the value itself.
        """
        if self._float_expected and value is not None:
            try:
                # It's faster to try... catch than to test np.size(value).
                # (but float(value) is slow to fail if value is None, so
                #  it is why we test it before)
                return float(value)
            except TypeError:
                pass
        return value


@deprecated(
    version="1.2.0", reason="Will be removed in version 2.0. Please use stdatm.AtmosphereSI instead"
)
class AtmosphereSI(Atmosphere):
    """Same as :class:`Atmosphere` except that altitudes are always in meters."""

    def __init__(self, altitude: Union[float, Sequence[float]], delta_t: float = 0.0):
        """
        :param altitude: altitude in meters
        :param delta_t: temperature increment (°C) applied to whole temperature profile
        """
        super().__init__(altitude, delta_t, altitude_in_feet=False)

    @property
    def altitude(self):
        """Altitude in meters."""
        return self.get_altitude(altitude_in_feet=False)
