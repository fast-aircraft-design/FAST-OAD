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
    Computes a flight path segment where altitude is modified with constant pitch angle.
    As a result, the slope angle and angle of attack are changing through time.
    Updates are based on longitudinal dynamics equations simplifies with the assumption of constant pitch angle.

    .. note:: **Setting target**

        Target is the safety altitude, or a speed:

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

    def complete_flight_point(self, flight_point: FlightPoint):
        """
        Redefinition, computes data for provided flight point.

        Assumes that it is already defined for time, altitude, mass,
        ground distance and speed (TAS, EAS, or Mach).

        :param flight_point: the flight point that will be completed in-place
        """
        flight_point.engine_setting = self.engine_setting

        self._complete_speed_values(flight_point)

        atm = AtmosphereSI(flight_point.altitude)
        reference_force = 0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_area

        if self.polar:
            flight_point.CL = flight_point.mass * g / reference_force
            flight_point.CD = self.polar.cd(flight_point.CL)
        else:
            flight_point.CL = flight_point.CD = 0.0
        flight_point.drag = flight_point.CD * reference_force

        self.compute_propulsion(flight_point)

        #Calls modified method to add gamma_dot to flight points.
        self.get_gamma_and_acceleration(flight_point)

    def get_distance_to_target(self, flight_points: List[FlightPoint]) -> float:
        current = flight_points[-1]

        if self.target.altitude is not None:
            return self.target.altitude - current.altitude

        raise FastFlightSegmentIncompleteFlightPoint(
            "No valid target definition for altitude change."
        )


    def compute_next_alpha(self, next_point: FlightPoint, previous_point: FlightPoint):
        """
        Computes angle of attacke (alpha) based on gamma_dot, using constant pitch angle assumption

        :param flight_point: parameters before propulsion model has been called

        :return: angle of attack in radians

        """
        time_step = next_point.time - previous_point.time

        #Constant pitch angle hypothesis
        next_point.alpha = (
                previous_point.alpha
                - time_step * previous_point.gamma_dot
        )


    def compute_next_gamma(self, next_point: FlightPoint, previous_point: FlightPoint):
        """
        Computes slope angle (gamma) based on gamma_dot

        :param flight_point: parameters before propulsion model has been called

        :return: slope angle in radians
        """
        time_step = next_point.time - previous_point.time
        next_point.slope_angle = (
                previous_point.slope_angle
                + time_step * previous_point.gamma_dot
        )

    def get_gamma_and_acceleration(self, flight_points: FlightPoint):
        """
        Redefinition : computes slope angle derivative (gamma_dot) and x-acceleration.

        :param flight_point: parameters after propulsion model has been called
                             (i.e. mass, thrust and drag are available)
        :return: slope angle in radians and acceleration in m**2/s
        """
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
