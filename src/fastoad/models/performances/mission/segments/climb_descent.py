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

from typing import Tuple, List

import numpy as np
import pandas as pd
from fastoad.models.performances.mission.flight_point import FlightPoint
from fastoad.models.performances.mission.segments.base import ManualThrustSegment
from fastoad.utils.physics import Atmosphere
from scipy.constants import g


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

    #: Using this value will tell to target the altitude with max lift/drag ratio.
    OPTIMAL_ALTITUDE = -10000.0

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        if self.target.altitude == self.OPTIMAL_ALTITUDE:
            self.target.CL = "optimal"

        if self.target.true_airspeed:
            if self.target.true_airspeed == "constant":
                self.target.true_airspeed = start.true_airspeed
            else:
                start.true_airspeed = self.target.true_airspeed
        elif self.target.equivalent_airspeed:
            if self.target.equivalent_airspeed == "constant":
                self.target.equivalent_airspeed = start.equivalent_airspeed
            start.true_airspeed = self.get_true_airspeed(
                self.target.equivalent_airspeed, start.altitude
            )

        return super().compute(start)

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        gamma = (thrust - drag) / mass / g
        return gamma, 0.0

    def target_is_attained(self, flight_points: List[FlightPoint]) -> bool:
        current = flight_points[-1]
        if self.target.CL == "optimal":
            self.target.altitude = self._get_optimal_altitude(
                current.mass, current.mach, current.altitude
            )

        tol = 1.0e-7  # Such accuracy is not needed, but ensures reproducibility of results.
        if self.target.altitude:
            return np.abs(current.altitude - self.target.altitude) <= tol
        elif self.target.true_airspeed:
            return np.abs(current.true_airspeed - self.target.true_airspeed) <= tol
        elif self.target.equivalent_airspeed:
            return np.abs(current.equivalent_airspeed - self.target.equivalent_airspeed) <= tol
        elif self.target.mach:
            return np.abs(current.mach - self.target.mach) <= tol

    def _compute_next_flight_point(self, flight_points: List[FlightPoint]) -> FlightPoint:
        start = flight_points[0]
        next_point = super()._compute_next_flight_point(flight_points)

        atm = Atmosphere(next_point.altitude, altitude_in_feet=False)

        if self.target.true_airspeed == "constant":
            next_point.true_airspeed = start.true_airspeed
        elif self.target.equivalent_airspeed == "constant":
            next_point.true_airspeed = self.get_true_airspeed(
                start.equivalent_airspeed, next_point.altitude
            )
        elif self.target.mach == "constant":
            next_point.true_airspeed = start.mach * atm.speed_of_sound

        if self.target.mach != "constant":
            # Mach number is capped by self.cruise_mach
            mach = next_point.true_airspeed / atm.speed_of_sound
            if mach > self.cruise_mach:
                next_point.true_airspeed = self.cruise_mach * atm.speed_of_sound

        return next_point
