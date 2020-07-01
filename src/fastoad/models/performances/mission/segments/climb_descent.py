"""Classes for climb/descent segments."""
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

import pandas as pd
from fastoad.utils.physics import AtmosphereSI
from scipy.constants import g

from .base import ManualThrustSegment
from ..flight_point import FlightPoint

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class ClimbDescentSegment(ManualThrustSegment):
    """
    Computes a flight path segment where altitude is modified with constant speed.

    .. note:: **Setting target altitude**

        Target altitude can be a float value (in **meters**), or can be set to
        :attr:`OPTIMAL_ALTITUDE`. In that case, the target altitude will be the altitude where
        maximum lift/drag ratio is achieved, depending on current mass and speed.

    .. note:: **Setting speed**

        Constant speed may be:

        - constant true airspeed
        - constant equivalent airspeed

        Definition of target decides the chosen constant speed:

        - if target has a numerical value for defined for :code:`true_airspeed` or
          :code:`equivalent_airspeed`, speed values of start flight points will be ignored and all
          computed flight points will have the target speed.

        - if target has :code:`"constant"` as definition for :code:`true_airspeed` of
          :code:`equivalent_airspeed`, all computed flight points will have the start speed.

    .. warning::

        Whatever the above setting, if :attr:`cruise_mach` attribute is set, speed will always be
        limited so that Mach number keeps lower or equal to this value.

    """

    def get_distance_to_target(self, flight_points: List[FlightPoint]) -> bool:
        current = flight_points[-1]
        if self.target.CL == "optimal":
            self.target.altitude = self._get_optimal_altitude(
                current.mass, current.mach, current.altitude
            )

        if self.target.altitude:
            return current.altitude - self.target.altitude
        elif self.target.true_airspeed:
            return current.true_airspeed - self.target.true_airspeed
        elif self.target.equivalent_airspeed:
            return current.equivalent_airspeed - self.target.equivalent_airspeed
        elif self.target.mach:
            return current.mach - self.target.mach

    #: Using this value will tell to target the altitude with max lift/drag ratio.
    OPTIMAL_ALTITUDE = -10000.0

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        if self.target.altitude == self.OPTIMAL_ALTITUDE:
            self.target.CL = "optimal"

        atm = AtmosphereSI(start.altitude)
        if self.target.equivalent_airspeed == "constant":
            start.true_airspeed = atm.get_true_airspeed(start.equivalent_airspeed)
        elif self.target.mach == "constant":
            start.true_airspeed = start.mach * atm.speed_of_sound

        return super().compute(start)

    # def _get_next_time_step(self, flight_points: List[FlightPoint]) -> float:
    #     start = flight_points[0]
    #     previous = flight_points[-1]
    #     # Time step evaluation
    #     # It will be the minimum value between the estimated time to reach the target and
    #     # and the default time step.
    #     # Checks are done against negative time step that could occur if thrust rate
    #     # creates acceleration when deceleration is needed, and so on...
    #     # They just create warning, in the (unlikely?) case it is isolated. If we keep
    #     # getting negative values, the global test about altitude and speed bounds will eventually
    #     # raise an Exception.
    #
    #     speed_time_step = altitude_time_step = self.time_step
    #     if previous.slope_angle != 0.0:
    #         if self.target.altitude:
    #             altitude_time_step = (
    #                 (self.target.altitude - previous.altitude)
    #                 / previous.true_airspeed
    #                 / np.sin(previous.slope_angle)
    #             )
    #
    #             if altitude_time_step < 0.0:
    #                 raise ValueError(
    #                     "Incorrect slope (%.2f°) at %s"
    #                     % (np.degrees(previous.slope_angle), previous)
    #                 )
    #                 # _LOGGER.warning(
    #                 #     "Incorrect slope (%.2f°) at %s"
    #                 #     % (np.degrees(previous.slope_angle), previous)
    #                 # )
    #                 altitude_time_step = self.time_step
    #         else:
    #             # Target is speed. Direct evaluation of time step is a bit tricky, so
    #             # we evaluate the new speed with standard time step and reduce it
    #             # if target has been exceeded.
    #             next_altitude = (
    #                 previous.altitude
    #                 + self.time_step * previous.true_airspeed * np.sin(previous.slope_angle)
    #             )
    #             atm = AtmosphereSI(next_altitude)
    #             if self.target.mach == "constant":
    #                 next_true_airspeed = start.mach * atm.speed_of_sound
    #             else:
    #                 next_true_airspeed = start.true_airspeed
    #
    #             if self.target.equivalent_airspeed:
    #                 next_equivalent_airspeed = atm.get_equivalent_airspeed(next_true_airspeed)
    #                 previous_to_target = (
    #                     self.target.equivalent_airspeed - previous.equivalent_airspeed
    #                 )
    #                 next_to_target = self.target.equivalent_airspeed - next_equivalent_airspeed
    #             else:  # target is true_airspeed
    #                 previous_to_target = self.target.true_airspeed - previous.true_airspeed
    #                 next_to_target = self.target.true_airspeed - next_true_airspeed
    #
    #             if previous_to_target * next_to_target < 0:
    #                 # target has been exceeded, time step need to be reduced.
    #                 speed_time_step = (
    #                     self.time_step * previous_to_target / (previous_to_target - next_to_target)
    #                 )
    #
    #     time_step = min(self.time_step, speed_time_step, altitude_time_step)
    #     return time_step

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        gamma = (thrust - drag) / mass / g
        return gamma, 0.0

    def _compute_next_flight_point(
        self, flight_points: List[FlightPoint], time_step: float
    ) -> FlightPoint:
        start = flight_points[0]
        next_point = super()._compute_next_flight_point(flight_points, time_step)

        atm = AtmosphereSI(next_point.altitude)

        if self.target.true_airspeed == "constant":
            next_point.true_airspeed = start.true_airspeed
        elif self.target.equivalent_airspeed == "constant":
            next_point.true_airspeed = atm.get_true_airspeed(start.equivalent_airspeed)
        elif self.target.mach == "constant":
            next_point.true_airspeed = start.mach * atm.speed_of_sound

        if self.target.mach != "constant":
            # Mach number is capped by self.cruise_mach
            mach = next_point.true_airspeed / atm.speed_of_sound
            if mach > self.cruise_mach:
                next_point.true_airspeed = self.cruise_mach * atm.speed_of_sound

        return next_point
