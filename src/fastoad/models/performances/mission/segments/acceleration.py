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
from fastoad.models.performances.mission.flight_point import FlightPoint
from fastoad.models.performances.mission.segments.base import ManualThrustSegment

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class AccelerationSegment(ManualThrustSegment):

    """
    Computes a flight path segment where true airspeed is modified with no change in altitude.
    """

    def _compute_next_flight_point(self, flight_points: List[FlightPoint]) -> FlightPoint:
        previous = flight_points[-1]
        next_point = FlightPoint()

        time_step = self._get_next_time_step(flight_points)

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

    def _get_next_time_step(self, flight_points: List[FlightPoint]) -> float:
        previous = flight_points[-1]

        # Time step evaluation
        # It will be the minimum value between the estimated time to reach the target and
        # and the default time step.
        # Checks are done against negative time step that could occur if thrust rate
        # creates acceleration when deceleration is needed, and so on...
        # They just create warning, in the (unlikely?) case it is isolated. If we keep
        # getting negative values, the global test about altitude and speed bounds will eventually
        # raise an Exception.
        speed_time_step = self.time_step
        if previous.acceleration != 0.0:
            if self.target.true_airspeed:
                speed_time_step = (
                    self.target.true_airspeed - previous.true_airspeed
                ) / previous.acceleration
            elif self.target.equivalent_airspeed:
                target_true_air_speed = self.get_true_airspeed(
                    self.target.equivalent_airspeed, previous.altitude
                )
                previous_true_air_speed = self.get_true_airspeed(
                    previous.equivalent_airspeed, previous.altitude
                )
                speed_time_step = (
                    target_true_air_speed - previous_true_air_speed
                ) / previous.acceleration

            if speed_time_step < 0.0:
                _LOGGER.warning(
                    "Incorrect acceleration (%.2f) at %s" % (previous.acceleration, previous)
                )
                speed_time_step = self.time_step

        time_step = min(self.time_step, speed_time_step)
        return time_step

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        acceleration = (thrust - drag) / mass
        return 0.0, acceleration

    def target_is_attained(self, flight_points: List[FlightPoint]) -> bool:
        tol = 1.0e-7  # Such accuracy is not needed, but ensures reproducibility of results.
        if self.target.true_airspeed:
            return np.abs(flight_points[-1].true_airspeed - self.target.true_airspeed) <= tol
        elif self.target.equivalent_airspeed:
            return (
                np.abs(flight_points[-1].equivalent_airspeed - self.target.equivalent_airspeed)
                <= tol
            )
