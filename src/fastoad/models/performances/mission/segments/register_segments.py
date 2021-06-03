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

from .altitude_change import AltitudeChangeSegment
from .cruise import BreguetCruiseSegment, ClimbAndCruiseSegment, OptimalCruiseSegment
from .hold import HoldSegment
from .speed_change import SpeedChangeSegment
from .taxi import TaxiSegment
from .transition import DummyTransitionSegment
from ..mission_definition.schema import SegmentDefinitions

segment_definition = {
    "altitude_change": AltitudeChangeSegment,
    "speed_change": SpeedChangeSegment,
    "cruise": ClimbAndCruiseSegment,
    "optimal_cruise": OptimalCruiseSegment,
    "holding": HoldSegment,
    "taxi": TaxiSegment,
    "transition": DummyTransitionSegment,
    "breguet": BreguetCruiseSegment,
}


for segment_name, segment_class in segment_definition.items():
    SegmentDefinitions.add_segment(segment_name, segment_class)
