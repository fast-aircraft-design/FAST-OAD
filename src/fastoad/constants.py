"""Definition of globally used constants."""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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

from enum import IntEnum, Enum


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

    TAKEOFF = 1
    CLIMB = 2
    CRUISE = 3
    IDLE = 4


class RangeCategory(Enum):
    """
    Definition of lower and upper limits of aircraft range categories, in Nautical Miles.

    can be used like::
        >>> range_value in RangeCategory.SHORT

    which is equivalent to:
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
