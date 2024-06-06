"""Classes for acceleration/deceleration segments."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
from typing import List

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.exceptions import FastFlightSegmentIncompleteFlightPoint
from fastoad.models.performances.mission.segments.base import RegisterSegment
from fastoad.models.performances.mission.segments.time_step_base import AbstractGroundSegment


@RegisterSegment("ground_speed_change")
@dataclass
class GroundSpeedChangeSegment(AbstractGroundSegment):
    """
    Computes a flight path segment where aircraft is accelerated or de-accelerated on the ground

    The target must define an airspeed (equivalent, true or Mach) value.
    """

    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:

        if target.true_airspeed is not None:
            return target.true_airspeed - flight_points[-1].true_airspeed
        if target.equivalent_airspeed is not None:
            return target.equivalent_airspeed - flight_points[-1].equivalent_airspeed
        if target.mach is not None:
            return target.mach - flight_points[-1].mach

        raise FastFlightSegmentIncompleteFlightPoint(
            "No valid target definition for airspeed change at takeoff."
        )
