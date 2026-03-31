"""Constants for the mission segments"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2026 ONERA & ISAE-SUPAERO
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

from enum import Enum


class ThrustRateOutOfBound(Enum):
    """
    Enum for thrust rate out of bound behavior in regulated altitude change segments.

    - EXTRAPOLATE: Allow thrust rate to go out of bounds (negative or > 1)
    - LIMIT: Force thrust rate to stay within bounds by switching to manual thrust
    """

    EXTRAPOLATE = "extrapolate"
    LIMIT = "limit"
