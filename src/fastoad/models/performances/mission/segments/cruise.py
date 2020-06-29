"""Classes for simulating cruise segments."""
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

from typing import List

import numpy as np
import pandas as pd
from fastoad.models.performances.mission.flight_point import FlightPoint
from fastoad.models.performances.mission.segments.base import AbstractSegment
from fastoad.utils.physics import Atmosphere
from scipy.constants import g


class OptimalCruiseSegment(AbstractSegment):

    """
    Class for computing flight segment at maximum lift/drag ratio.

    Mach is considered constant. Altitude is set to get the optimum CL according
    to current mass.
    """

    def __init__(self, *args, **kwargs):
        """

        :ivar cruise_mach: cruise Mach number. Mandatory before running :meth:`compute`.
                           Can be set at instantiation using a keyword argument.
        """

        self._keyword_args["cruise_mach"] = None

        super().__init__(*args, **kwargs)

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        self.target.ground_distance = self.target.ground_distance + start.ground_distance
        return super().compute(start)

    def target_is_attained(self, flight_points: List[FlightPoint]) -> bool:
        current = flight_points[-1]
        return np.abs(current.ground_distance - self.target.ground_distance) <= 1.0

    def _compute_next_flight_point(self, flight_points: List[FlightPoint]) -> FlightPoint:
        previous = flight_points[-1]
        next_point = FlightPoint()

        time_step = (
            self.target.ground_distance - previous.ground_distance
        ) / previous.true_airspeed
        time_step = min(self.time_step, time_step)

        next_point.mass = previous.mass - previous.sfc * previous.thrust * time_step
        next_point.mach = self.cruise_mach
        next_point.altitude = (
            previous.altitude
        )  # will provide an initial guess for computing optimal altitude

        next_point.time = previous.time + time_step
        next_point.ground_distance = previous.ground_distance + previous.true_airspeed * time_step
        return next_point

    def _complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point.

        Assumes that it is already defined for time and mass.

        :param flight_point: the flight point that will be completed in-place
        """

        flight_point.altitude = self._get_optimal_altitude(
            flight_point.mass, self.cruise_mach, flight_point.altitude
        )
        atm = Atmosphere(flight_point.altitude, altitude_in_feet=False)
        flight_point.mach = self.cruise_mach
        flight_point.true_airspeed = atm.speed_of_sound * flight_point.mach

        flight_point.engine_setting = self.engine_setting

        reference_force = (
            0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_surface
        )
        flight_point.CL = flight_point.mass * g / reference_force
        flight_point.CD = self.polar.cd(flight_point.CL)
        drag = flight_point.CD * reference_force

        (
            flight_point.sfc,
            flight_point.thrust_rate,
            flight_point.thrust,
        ) = self.propulsion.compute_flight_points(
            flight_point.mach, flight_point.altitude, flight_point.engine_setting, thrust=drag
        )
        flight_point.slope_angle, flight_point.acceleration = 0.0, 0.0
