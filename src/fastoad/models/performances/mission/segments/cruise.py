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

from typing import List, Tuple

import pandas as pd
from fastoad.utils.physics import AtmosphereSI

from .base import AbstractSegment
from ..flight_point import FlightPoint


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

        if "time_step" not in kwargs:
            kwargs["time_step"] = 60.0
        super().__init__(*args, **kwargs)

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        self.target.ground_distance = self.target.ground_distance + start.ground_distance
        start.altitude = self._get_optimal_altitude(start.mass, self.cruise_mach)
        start.mach = self.cruise_mach
        return super().compute(start)

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        return 0.0, 0.0

    def _compute_propulsion(self, flight_point: FlightPoint, drag: float):
        (
            flight_point.sfc,
            flight_point.thrust_rate,
            flight_point.thrust,
        ) = self.propulsion.compute_flight_points(
            flight_point.mach, flight_point.altitude, flight_point.engine_setting, thrust=drag,
        )

    def _compute_next_flight_point(
        self, flight_points: List[FlightPoint], time_step: float
    ) -> FlightPoint:
        previous = flight_points[-1]
        next_point = FlightPoint()

        next_point.time = previous.time + time_step
        next_point.mass = previous.mass - previous.sfc * previous.thrust * time_step
        next_point.ground_distance = previous.ground_distance + previous.true_airspeed * time_step
        next_point.altitude = self._get_optimal_altitude(
            next_point.mass, self.cruise_mach, altitude_guess=previous.altitude
        )
        atm = AtmosphereSI(next_point.altitude)
        next_point.true_airspeed = self.cruise_mach * atm.speed_of_sound

        return next_point

    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> bool:
        current = flight_points[-1]
        return current.ground_distance - self.target.ground_distance
