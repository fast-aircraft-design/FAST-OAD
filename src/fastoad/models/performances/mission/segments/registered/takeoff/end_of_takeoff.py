"""Classes for climb/descent segments."""
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
from fastoad.models.performances.mission.segments.time_step_base import AbstractTakeOffSegment


# FIXME: This class is a bit awkward, because get_gamma_and_acceleration() knows
#       only the current flight point, which prevents from using the slope derivative.
#       A redefinition of the abstract class is needed.


@RegisterSegment("end_of_takeoff")
@dataclass
class EndOfTakeoffSegment(AbstractTakeOffSegment):
    """
    Computes a flight path segment where altitude is modified with constant pitch angle.
    As a result, the slope angle and angle of attack are changing through time.
    Updates are based on longitudinal dynamics equations simplifies with the assumption
    of constant pitch angle.

    .. note:: **Setting target**

        Target is an altitude and should be set to the safety altitude.

    """

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

        self.compute_next_gamma(next_point, previous)
        return next_point

    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:
        current = flight_points[-1]

        if target.altitude is not None:
            return target.altitude - current.altitude

        raise FastFlightSegmentIncompleteFlightPoint(
            "No valid target definition for altitude change."
        )

    def get_next_alpha(self, previous_point: FlightPoint, time_step: float) -> float:
        """
        Computes angle of attack (alpha) based on gamma_dot, using constant pitch angle assumption.

        :param previous_point: the flight point from which next alpha is computed
        :param time_step: the duration between computed flight point and previous_point
        """

        return previous_point.alpha - time_step * previous_point.slope_angle_derivative

    @staticmethod
    def compute_next_gamma(next_point: FlightPoint, previous_point: FlightPoint):
        """
        Computes slope angle (gamma) based on gamma_dot

        :param next_point: the next flight point
        :param previous_point: the flight point from which next gamma is computed
        """
        time_step = next_point.time - previous_point.time
        next_point.slope_angle = (
            previous_point.slope_angle + time_step * previous_point.slope_angle_derivative
        )
