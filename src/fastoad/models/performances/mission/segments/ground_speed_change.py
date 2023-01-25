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
from dataclasses import dataclass
from typing import List

from scipy.constants import g

from fastoad.model_base import FlightPoint
from .base import GroundSegment
from ..exceptions import FastFlightSegmentIncompleteFlightPoint

_LOGGER = logging.getLogger(__name__)  # Logger for this module


@dataclass
class GroundSpeedChangeSegment(GroundSegment, mission_file_keyword="ground_speed_change"):
    """
    Computes a flight path segment where aircraft is accelerated or de-accelerated on the ground

    The target must define an airspeed (equivalent, true or Mach) value.
    """

    def complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point.

        Assumes that it is already defined for time, altitude, mass,
        ground distance and speed (TAS, EAS, or Mach).

        :param flight_point: the flight point that will be completed in-place
        """
        flight_point.engine_setting = self.engine_setting

        self._complete_speed_values(flight_point)

        # initialize alpha, and gamma_dot
        # alpha = 0
        # gamma_dot = 0

        flight_point.alpha = self.alpha
        # flight_point.slope_angle_derivative = gamma_dot

        atm = self._get_atmosphere_point(flight_point.altitude)
        reference_force = 0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_area

        if self.polar:
            CL = self.polar.cl(self.alpha)
            CD = self.polar_modifier.ModifyPolar(self.polar, flight_point).cd(CL)
            # self.polar_modifier.ModifyPolar(self.polar, flight_point)
            flight_point.CD = CD
            flight_point.CL = CL
        else:
            flight_point.CL = flight_point.CD = 0.0
        flight_point.drag = flight_point.CD * reference_force
        flight_point.lift = flight_point.CL * reference_force

        self.compute_propulsion(flight_point)
        flight_point.slope_angle, flight_point.acceleration = self.get_gamma_and_acceleration(
            flight_point
        )

    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:
        """
        It is interesting to set equivalent speed or Mach target for non isa conditions
        """
        if target.true_airspeed is not None:
            return target.true_airspeed - flight_points[-1].true_airspeed
        if target.equivalent_airspeed is not None:
            return target.equivalent_airspeed - flight_points[-1].equivalent_airspeed
        if target.mach is not None:
            return target.mach - flight_points[-1].mach

        raise FastFlightSegmentIncompleteFlightPoint(
            "No valid target definition for airspeed change at takeoff."
        )

    def get_gamma_and_acceleration(self, flight_point: FlightPoint):
        """
        For ground segment, gamma is assumed always 0 and wheel friction is considered
        (with or without brake)
        """
        mass = flight_point.mass
        drag_aero = flight_point.drag
        lift = flight_point.lift
        thrust = flight_point.thrust

        drag = drag_aero + (mass * g - lift) * self.wheels_friction

        # edit flight_point fields
        flight_point.drag = drag

        acceleration = (thrust - drag) / mass

        return 0.0, acceleration
