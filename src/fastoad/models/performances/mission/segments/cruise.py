"""Classes for simulating cruise segments."""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

from typing import List

import pandas as pd
from fastoad.base.flight_point import FlightPoint

from .base import RegulatedThrustSegment


class CruiseSegment(RegulatedThrustSegment):
    """
    Class for computing cruise flight segment at constant altitude.

    Mach is considered constant, equal to Mach at starting point.
    Altitude is constant.
    Target is a specified ground_distance. The target definition indicates
    the ground_distance to be covered during the segment, independently of
    the initial value.
    """

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        if start.ground_distance:
            self.target.ground_distance = self.target.ground_distance + start.ground_distance
        return super().compute_from(start)

    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> bool:
        current = flight_points[-1]
        return self.target.ground_distance - current.ground_distance


class OptimalCruiseSegment(CruiseSegment):
    """
    Class for computing cruise flight segment at maximum lift/drag ratio.

    Mach is considered constant, equal to Mach at starting point. Altitude is set **at every
    point** to get the optimum CL according to current mass.
    """

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        start.altitude = self._get_optimal_altitude(start.mass, start.mach)
        return super().compute_from(start)

    def _compute_next_altitude(self, next_point, previous_point):
        next_point.altitude = self._get_optimal_altitude(
            next_point.mass, previous_point.mach, altitude_guess=previous_point.altitude
        )
