"""Classes for climb/descent segments."""
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
from copy import copy
from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd
from numpy import cos, sin
from scipy.constants import foot, g
from stdatm import AtmosphereSI

from fastoad.model_base import FlightPoint
from .base import ManualThrustSegment
from ..exceptions import FastFlightSegmentIncompleteFlightPoint
from ..util import get_closest_flight_level

_LOGGER = logging.getLogger(__name__)  # Logger for this module


@dataclass
class EndOfTakoffSegment(ManualThrustSegment, mission_file_keyword="end_of_takeoff"):
    """
    Computes a flight path segment where altitude is modified with constant speed.

    .. note:: **Setting speed**

        Constant speed may be:

        - constant true airspeed (TAS)
        - constant equivalent airspeed (EAS)
        - constant Mach number

        Target should have :code:`"constant"` as definition for one parameter among
        :code:`true_airspeed`, :code:`equivalent_airspeed` or :code:`mach`.
        All computed flight points will use the corresponding **start** value.
        The two other speed values will be computed accordingly.

        If not "constant" parameter is set, constant TAS is assumed.

    .. note:: **Setting target**

        Target can be an altitude, or a speed:

        - Target altitude can be a float value (in **meters**), or can be set to:

            - :attr:`OPTIMAL_ALTITUDE`: in that case, the target altitude will be the altitude
              where maximum lift/drag ratio is achieved for target speed, depending on current mass.
            - :attr:`OPTIMAL_FLIGHT_LEVEL`: same as above, except that altitude will be rounded to
              the nearest flight level (multiple of 100 feet).

        - For a speed target, as explained above, one value  TAS, EAS or Mach must be
          :code:`"constant"`. One of the two other ones can be set as target.

        In any case, the achieved value will be capped so it respects
        :attr:`maximum_flight_level`.

    """

    time_step: float = 0.05

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
        self.compute_next_gamma(next_point, previous)
        return next_point

    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> float:
        current = flight_points[-1]

        if self.target.altitude is not None:
            return self.target.altitude - current.altitude

        raise FastFlightSegmentIncompleteFlightPoint(
            "No valid target definition for altitude change."
        )


    def compute_next_alpha(self, next_point: FlightPoint, previous_point: FlightPoint):
        time_step = next_point.time - previous_point.time

        #Constant pitch angle hypothesis
        next_point.alpha = (
                previous_point.alpha
                - time_step * previous_point.gamma_dot
        )


    def compute_next_gamma(self, next_point: FlightPoint, previous_point: FlightPoint):
        time_step = next_point.time - previous_point.time
        next_point.slope_angle = (
                previous_point.slope_angle
                + time_step * previous_point.gamma_dot
        )

    def _get_gamma_and_acceleration(self, flight_points: List[FlightPoint]):

        thrust = flight_points.thrust
        drag = flight_points.drag
        mass = flight_points.mass
        airspeed = flight_points.true_airspeed
        alpha = flight_points.alpha
        gamma = flight_points.slope_angle
        altitude = flight_points.altitude

        atm = AtmosphereSI(flight_points.altitude)

        CL = self.polar.cl(alpha)
        CD = self.polar.cd_ground(cl=CL, altitude=altitude)
        drag_aero = 0.5 * atm.density * self.reference_area * airspeed ** 2 * CD
        lift = 0.5 * atm.density * self.reference_area * airspeed ** 2 * CL
        
        gamma_dot = (thrust*sin(alpha) + lift - mass*g*cos(gamma)) / mass / airspeed
        acceleration = (thrust*cos(alpha) - drag_aero - mass*g*sin(gamma))/mass
        flight_points.acceleration = acceleration
        flight_points.gamma_dot = gamma_dot

