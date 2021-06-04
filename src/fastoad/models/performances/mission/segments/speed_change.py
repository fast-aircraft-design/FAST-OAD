"""Classes for acceleration/deceleration segments."""
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

import logging
from typing import List, Tuple

from fastoad.model_base import FlightPoint
from .base import ManualThrustSegment
from ..exceptions import FastFlightSegmentIncompleteFlightPoint

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class SpeedChangeSegment(ManualThrustSegment, mission_file_keyword="speed_change"):
    """
    Computes a flight path segment where speed is modified with no change in altitude.

    The target must define a speed value among true_airspeed, equivalent_airspeed
    and mach.
    """

    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> float:
        if self.target.true_airspeed is not None:
            return self.target.true_airspeed - flight_points[-1].true_airspeed
        if self.target.equivalent_airspeed is not None:
            return self.target.equivalent_airspeed - flight_points[-1].equivalent_airspeed
        if self.target.mach is not None:
            return self.target.mach - flight_points[-1].mach

        raise FastFlightSegmentIncompleteFlightPoint(
            "No valid target definition for altitude change."
        )

    def _get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        acceleration = (thrust - drag) / mass
        return 0.0, acceleration
