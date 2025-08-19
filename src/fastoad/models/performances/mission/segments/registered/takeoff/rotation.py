"""Classes for acceleration/deceleration segments."""

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

        lift = 0.5 * atm.density * self.reference_area * airspeed**2 * CL * cos(
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
