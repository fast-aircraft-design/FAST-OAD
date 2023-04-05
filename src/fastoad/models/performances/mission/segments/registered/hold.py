"""Class for simulating hold segment."""
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

from dataclasses import dataclass

from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.segments.time_step_base import (
    AbstractFixedDurationSegment,
    AbstractRegulatedThrustSegment,
)


@RegisterSegment("holding")
@dataclass
class HoldSegment(AbstractRegulatedThrustSegment, AbstractFixedDurationSegment):
    """
    Class for computing hold flight segment.

    Mach is considered constant, equal to Mach at starting point.
    Altitude is constant.
    Target is a specified time. The target definition indicates
    the time duration of the segment, independently of the initial time value.
    """
