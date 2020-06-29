"""Classes for Taxi sequences."""
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

import numpy as np
import pandas as pd
from fastoad.models.performances.mission.flight_point import FlightPoint
from fastoad.models.performances.mission.segments.base import ManualThrustSegment


class TaxiSegment(ManualThrustSegment):
    def compute(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        target = FlightPoint(target)
        self.time_step = target.time  # This computation needs only one time step

        target.time = target.time + start.time
        return super().compute(start, target)

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        return 0.0, 0.0

    def target_is_attained(self, flight_points: List[FlightPoint], target: FlightPoint) -> bool:
        current = flight_points[-1]
        return np.abs(current.time - target.time) <= 1.0e-7
