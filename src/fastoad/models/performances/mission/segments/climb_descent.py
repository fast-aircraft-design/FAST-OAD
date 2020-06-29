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

    Constant speed may be:

        - constant true airspeed
        - constant equivalent airspeed

    The speed will be constrained according to definition of target in :meth:`compute`.
    Speed value from starting point will be ignored.

    Additionally, if :attr:`cruise_mach` attribute is set, speed will always be limited
    so that Mach number keeps lower or equal to this value.
    """

    #: Using this value will tell tell to target the altitude with max lift/drag ratio.
    OPTIMAL_ALTITUDE = -10000.0

    def __init__(self, *args, **kwargs):

        self._keyword_args["keep_true_airspeed"] = True
        super().__init__(*args, **kwargs)

    def compute(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        target = FlightPoint(target)
        if target.altitude == self.OPTIMAL_ALTITUDE:
            target.CL = "optimal"

        if target.true_airspeed:
            start.true_airspeed = target.true_airspeed
        elif target.equivalent_airspeed:
            start.true_airspeed = self.get_true_airspeed(target.equivalent_airspeed, start.altitude)

        return super().compute(start, target)

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        gamma = (thrust - drag) / mass / g
        return gamma, 0.0

    def target_is_attained(self, flight_points: List[FlightPoint], target: FlightPoint) -> bool:
        current = flight_points[-1]
        if target.CL == "optimal":
            target.altitude = self._get_optimal_altitude(
                current.mass, current.mach, current.altitude
            )

        tol = 1.0e-7  # Such accuracy is not needed, but ensures reproducibility of results.
        return np.abs(current.altitude - target.altitude) <= tol

    def _compute_next_flight_point(self, previous: FlightPoint, target: FlightPoint) -> FlightPoint:
        next_point = super()._compute_next_flight_point(previous, target)

        if target.true_airspeed:
            next_point.true_airspeed = target.true_airspeed
        elif target.equivalent_airspeed:
            next_point.true_airspeed = self.get_true_airspeed(
                target.equivalent_airspeed, next_point.altitude
            )

        # Mach number is capped by self.cruise_mach
        atm = Atmosphere(next_point.altitude, altitude_in_feet=False)
        mach = next_point.true_airspeed / atm.speed_of_sound
        if mach > self.cruise_mach:
            next_point.true_airspeed = self.cruise_mach * atm.speed_of_sound

        return next_point
