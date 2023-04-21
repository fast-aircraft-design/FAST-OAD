"""Class for takeoff sequence"""
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

import numpy as np

from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from fastoad.models.performances.mission.segments.base import RegisterSegment
from fastoad.models.performances.mission.segments.macro_segments import MacroSegmentMeta
from .end_of_takeoff import EndOfTakeoffSegment
from .rotation import RotationSegment
from ..ground_speed_change import GroundSpeedChangeSegment


@RegisterSegment("takeoff")
@dataclass
class TakeOffSequence(
    metaclass=MacroSegmentMeta,
    cls_sequence=[GroundSpeedChangeSegment, RotationSegment, EndOfTakeoffSegment],
):
    """
    This class does a time-step simulation of a full takeoff:

    - ground speed acceleration up to :attr:`rotation_equivalent_airspeed`
    - rotation
    - climb up to altitude provided in :attr:`target` (safety altitude)
    """

    #: Equivalent airspeed to reach for starting aircraft rotation.
    rotation_equivalent_airspeed: float = MANDATORY_FIELD

    #: Angle of attack (in radians) where tail strike is expected. Default value
    #: is good for SMR aircraft.
    rotation_alpha_limit: float = np.radians(13.5)

    # Used time step for computing the takeoff part after rotation.
    end_time_step: float = 0.05

    def build_sequence(self):
        """
        Instantiates all segments, using dataclass field values of this macro-segment.

        Note: this method is called each time a dataclass field value is modified.
        """
        super().build_sequence()

        ground, rotation, end = self[:]

        ground.target = FlightPoint(equivalent_airspeed=self.rotation_equivalent_airspeed)

        rotation.target = FlightPoint()
        rotation.rotation_rate = self.rotation_rate
        rotation.alpha_limit = self.rotation_alpha_limit

        end.time_step = self.end_time_step
