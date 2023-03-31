"""Classes for acceleration/deceleration segments."""
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

import logging
from dataclasses import dataclass
from typing import List

from numpy import cos, pi, sin
from scipy.constants import g

from fastoad.model_base import FlightPoint
from ..base import GroundSegment, RegisterSegment

_LOGGER = logging.getLogger(__name__)  # Logger for this module


@RegisterSegment("rotation")
@dataclass
class RotationSegment(GroundSegment):
    """
    Computes a flight path segment with constant rotation rate while on ground
    and accelerating.

    The target is the lift-off. A protection is included is the aircraft reaches
    alpha_limit (tail-strike).
    """

    # The following default values are good for SMR type of aircraft.
    # But users may be willing to test takeoff by changing these values.
    rotation_rate: float = 3 / 180 * pi  # CS-25 rotation rate
    alpha_limit: float = 13.5 / 180 * pi

    def compute_next_flight_point(
        self, flight_points: List[FlightPoint], time_step: float
    ) -> FlightPoint:
        """
        Computes time, altitude, speed, mass and ground distance of next flight point.

        :param flight_points: previous flight points
        :param time_step: time step for computing next point
        :return: the computed next flight point
        """
        previous = flight_points[-1]
        next_point = super().compute_next_flight_point(flight_points, time_step)

        self.compute_next_alpha(next_point, previous)
        return next_point

    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:

        # compute lift, including thrust projection, compare with weight
        current = flight_points[-1]

        atm = self._get_atmosphere_point(current.altitude)
        airspeed = current.true_airspeed
        mass = current.mass
        alpha = current.alpha
        CL = current.CL
        thrust = current.thrust

        lift = 0.5 * atm.density * self.reference_area * airspeed ** 2 * CL * cos(
            alpha
        ) + thrust * sin(alpha)

        if alpha >= self.alpha_limit:
            # Tail strick, issue warning and continue accelerating without rotation
            self.rotation_rate = 0.0
            _LOGGER.warning("TAIL STRIKE during take-off, consider increasing VR.")

        return lift - mass * g

    def compute_next_alpha(self, next_point: FlightPoint, previous_point: FlightPoint):
        """
        Determine the next AoA based on imposed rotation rate

        :param next_point: the next flight point
        :param previous_point: the flight point from which next alpha is computed
        """
        time_step = next_point.time - previous_point.time
        next_point.alpha = previous_point.alpha + time_step * self.rotation_rate
