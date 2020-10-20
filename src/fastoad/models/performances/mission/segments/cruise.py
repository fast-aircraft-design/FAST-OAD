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

from copy import deepcopy
from typing import List

import pandas as pd
from scipy.constants import foot

from fastoad.base.dict import AddKeyAttributes
from fastoad.base.flight_point import FlightPoint
from .base import RegulatedThrustSegment
from ..util import get_closest_flight_level


@AddKeyAttributes({"climb_class": None, "maximum_flight_level": 500.0})
class CruiseSegment(RegulatedThrustSegment):
    """
    Class for computing cruise flight segment at constant altitude.

    Mach is considered constant, equal to Mach at starting point.
    Altitude is constant.
    Target is a specified ground_distance. The target definition indicates
    the ground_distance to be covered during the segment, independently of
    the initial value.
    """

    OPTIMAL_FLIGHT_LEVEL = -20000.0

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        if start.ground_distance:
            self.target.ground_distance = self.target.ground_distance + start.ground_distance

        if self.target.altitude == self.OPTIMAL_FLIGHT_LEVEL:
            new_cruise = deepcopy(self)
            new_cruise.target.altitude = None

            # Go to the next flight level, or keep altitude if already at a flight level
            cruise_altitude = get_closest_flight_level(start.altitude - 1.0e-3)
            results = self._climb_to_altitude_and_cruise(start, cruise_altitude, new_cruise)
            mass_loss = start.mass - results.mass.iloc[-1]

            go_to_next_level = True

            while go_to_next_level:
                old_mass_loss = mass_loss
                cruise_altitude = get_closest_flight_level(cruise_altitude + 1.0e-3)
                if cruise_altitude > self.maximum_flight_level * 100.0 * foot:
                    break

                new_results = self._climb_to_altitude_and_cruise(start, cruise_altitude, new_cruise)
                mass_loss = start.mass - new_results.mass.iloc[-1]

                go_to_next_level = mass_loss < old_mass_loss
                if go_to_next_level:
                    results = new_results

            return results

        return super().compute_from(start)

    def _climb_to_altitude_and_cruise(
        self, start: FlightPoint, cruise_altitude: float, cruise_definition: "CruiseSegment"
    ):
        climb_definition = deepcopy(self.climb_class)
        climb_definition.target = FlightPoint(altitude=cruise_altitude, mach="constant")
        climb_points = climb_definition.compute_from(start)

        cruise_start = FlightPoint(climb_points.iloc[-1])
        cruise_definition.target.ground_distance = (
            self.target.ground_distance - cruise_start.ground_distance
        )
        cruise_points = cruise_definition.compute_from(cruise_start)

        return pd.concat([climb_points, cruise_points]).reset_index(drop=True)

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

    def _compute_next_altitude(self, next_point: FlightPoint, previous_point: FlightPoint):
        next_point.altitude = self._get_optimal_altitude(
            next_point.mass, previous_point.mach, altitude_guess=previous_point.altitude
        )
