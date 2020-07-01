"""Classes for acceleration/deceleration segments."""
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

import logging
from typing import Tuple, List

import numpy as np

from .base import ManualThrustSegment
from ..flight_point import FlightPoint

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class AccelerationSegment(ManualThrustSegment):
    """
    Computes a flight path segment where true airspeed is modified with no change in altitude.
    """

    def _compute_next_flight_point(
        self, flight_points: List[FlightPoint], time_step: float
    ) -> FlightPoint:
        previous = flight_points[-1]
        next_point = FlightPoint()

        next_point.altitude = previous.altitude + time_step * previous.true_airspeed * np.sin(
            previous.slope_angle
        )
        next_point.true_airspeed = previous.true_airspeed + time_step * previous.acceleration
        next_point.mass = previous.mass - previous.sfc * previous.thrust * time_step
        next_point.time = previous.time + time_step
        next_point.ground_distance = (
            previous.ground_distance
            + previous.true_airspeed * time_step * np.cos(previous.slope_angle)
        )
        return next_point

    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> bool:
        if self.target.true_airspeed:
            return flight_points[-1].true_airspeed - self.target.true_airspeed
        elif self.target.equivalent_airspeed:
            return flight_points[-1].equivalent_airspeed - self.target.equivalent_airspeed

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        acceleration = (thrust - drag) / mass
        return 0.0, acceleration
