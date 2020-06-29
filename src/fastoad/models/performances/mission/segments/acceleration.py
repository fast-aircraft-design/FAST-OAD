"""Classes for acceleration/deceleration segments."""
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
from fastoad.models.performances.mission.flight_point import FlightPoint
from fastoad.models.performances.mission.segments.base import ManualThrustSegment


class AccelerationSegment(ManualThrustSegment):

    """
    Computes a flight path segment where true airspeed is modified with no change in altitude.
    """

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        acceleration = (thrust - drag) / mass
        return 0.0, acceleration

    def target_is_attained(self, flight_points: List[FlightPoint]) -> bool:
        tol = 1.0e-7  # Such accuracy is not needed, but ensures reproducibility of results.
        return np.abs(flight_points[-1].true_airspeed - self.target.true_airspeed) <= tol
