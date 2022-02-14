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
from numpy import pi, sin, cos
from stdatm import AtmosphereSI

from fastoad.model_base import FlightPoint
from .base import ManualThrustSegment
from ..exceptions import FastFlightSegmentIncompleteFlightPoint
from scipy.constants import g

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class RotationSegment(ManualThrustSegment, mission_file_keyword="rotation"):
    """
    Computes a flight path segment with constant rotation rate while on ground and accelerating

    The target must define an alpha limit value.
    """

    # TO DO : leave the possibility to modify for CS23
    rotation_rate: float = 3/180*pi #CS-25 rotation rate

    time_step: float = 0.1

    dynamic_var = {'alpha': {'name': 'alpha', 'unit': 'rad'},
                   'alpha_dot': {'name': 'alpha_dot', 'unit': 'rad/s'},
                   'gamma_dot': {'name': 'gamma_dot', 'unit': 'rad/s'},
                   }

    # friction_nobrake: float = 0.03

    alpha_limit = 13.5/180*pi

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
        self.compute_next_alpha(next_point, previous )
        return next_point

    def complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point.

        Assumes that it is already defined for time, altitude, mass,
        ground distance and speed (TAS, EAS, or Mach).

        :param flight_point: the flight point that will be completed in-place
        """
        flight_point.engine_setting = self.engine_setting

        self._complete_speed_values(flight_point)

        atm = AtmosphereSI(flight_point.altitude)
        reference_force = 0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_area

        if self.polar:
            alpha = flight_point.alpha
            CL = self.polar.cl(alpha)
            CD = self.polar.cd_ground(cl=CL, altitude=flight_point.altitude)
            flight_point.CL = CL
            flight_point.CD = CD
        else:
            flight_point.CL = flight_point.CD = 0.0
        flight_point.drag = flight_point.CD * reference_force
        flight_point.lift = flight_point.CL * reference_force

        self.compute_propulsion(flight_point)
        flight_point.slope_angle, flight_point.acceleration = self.get_gamma_and_acceleration(
            flight_point
        )

    def get_distance_to_target(self, flight_points: List[FlightPoint]) -> float:

        #compute lift, including thrust projection, compare with weight
        current = flight_points[-1]

        atm = AtmosphereSI(current.altitude)
        airspeed = current.true_airspeed
        mass = current.mass
        alpha = current.alpha
        CL = self.polar.cl(alpha)
        thrust = current.thrust

        lift = 0.5 * atm.density * self.reference_area * airspeed ** 2 * CL * cos(alpha) + thrust * sin(alpha)
        if alpha <= self.alpha_limit:
            return lift - mass * g

        raise FastFlightSegmentIncompleteFlightPoint(
            "Alpha limit reached, aircraft cannot takeoff before tailstrick, consider increasing Vr."
        )

    def compute_next_alpha(self, next_point: FlightPoint, previous_point: FlightPoint):

        time_step = next_point.time - previous_point.time
        next_point.alpha = (
                previous_point.alpha
                + time_step * self.rotation_rate
        )

    def get_gamma_and_acceleration(self, flight_points: FlightPoint):

        mass = flight_points.mass
        drag_aero = flight_points.drag
        lift = flight_points.lift
        thrust = flight_points.thrust

        drag = drag_aero + (mass*g-lift)*self.friction_nobrake

        # edit flight_points fields
        flight_points.drag = drag

        acceleration = (thrust - drag) / mass

        return 0.0, acceleration
