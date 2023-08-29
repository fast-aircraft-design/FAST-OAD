"""Definition of globally used constants."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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

from aenum import Enum, IntEnum, extend_enum


class FlightPhase(Enum):
    """
    Enumeration of flight phases.
    """

    TAXI_OUT = "taxi_out"
    TAKEOFF = "takeoff"
    INITIAL_CLIMB = "initial_climb"
    CLIMB = "climb"
    CRUISE = "cruise"
    DESCENT = "descent"
    LANDING = "landing"
    TAXI_IN = "taxi_in"


class EngineSetting(IntEnum):
    """
    Enumeration of engine settings.
    """

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name.lower() == other.lower()

        return super().__eq__(other)

    def __hash__(self):
        return self.value

    @classmethod
    def convert(cls, name: str) -> "EngineSetting":
        """
        :param name:
        :return: the EngineSetting instance that matches the provided name (case-insensitive)
        """
        for instance in cls:
            if instance.name.lower() == name.lower():
                return instance

        return None


# Using the extensibility of EngineSetting is not needed here, but it allows to
# test it.
extend_enum(EngineSetting, "TAKEOFF")
extend_enum(EngineSetting, "CLIMB")
extend_enum(EngineSetting, "CRUISE")
extend_enum(EngineSetting, "IDLE")


class RangeCategory(Enum):
    """
    Definition of lower and upper limits of aircraft range categories, in Nautical Miles.

    can be used like::

        >>> range_value = 800.
        >>> range_value in RangeCategory.SHORT
        True

    which is equivalent to::

        >>>  RangeCategory.SHORT.min() <= range_value <= RangeCategory.SHORT.max()
    """

    SHORT = (0.0, 1500.0)
    SHORT_MEDIUM = (1500.0, 3000.0)
    MEDIUM = (3000.0, 4500.0)
    LONG = (4500.0, 6000.0)
    VERY_LONG = (6000.0, 1.0e6)

    def min(self):
        """
        :return: minimum range in category
        """
        return self.value[0]

    def max(self):
        """
        :return: maximum range in category
        """
        return self.value[1]

    def __contains__(self, range_value):
        """
        :param range_value:
        :return: True if rang_value is inside range limits, False otherwise
        """
        return self.min() <= range_value <= self.max()
