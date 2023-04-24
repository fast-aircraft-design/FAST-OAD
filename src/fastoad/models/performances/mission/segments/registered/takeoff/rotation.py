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

import numpy as np
from numpy import cos, sin
from scipy.constants import g

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.segments.base import RegisterSegment
from fastoad.models.performances.mission.segments.time_step_base import AbstractGroundSegment

_LOGGER = logging.getLogger(__name__)  # Logger for this module


@RegisterSegment("rotation")
@dataclass
class RotationSegment(AbstractGroundSegment):
    """
    Computes a flight path segment with constant rotation rate while on ground
    and accelerating.

    The target is the lift-off. A protection is included is the aircraft reaches
    alpha_limit (tail-strike).
    """

    #: Rotation rate in radians/s, i.e. derivative of angle of attack.
    #: Default value is CS-25 specification.
    rotation_rate: float = np.radians(3)

    #: Angle of attack (in radians) where tail strike is expected. Default value
    #: is good for SMR aircraft.
    alpha_limit: float = np.radians(13.5)

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
            # Tail strike, issue warning and continue accelerating without rotation
            self.rotation_rate = 0.0
            _LOGGER.warning("TAIL STRIKE during take-off, consider increasing VR.")

        return lift - mass * g

    def get_next_alpha(self, previous_point: FlightPoint, time_step: float) -> float:
        """
        Determine the next AoA based on imposed rotation rate.

        :param previous_point: the flight point from which next alpha is computed
        :param time_step: the duration between computed flight point and previous_point
        """
        return previous_point.alpha + time_step * self.rotation_rate
