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

import pandas as pd

from .base import ManualThrustSegment
from ..flight_point import FlightPoint


class TaxiSegment(ManualThrustSegment):
    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> bool:
        current = flight_points[-1]
        return self.target.time - current.time

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        self.time_step = self.target.time  # This computation needs only one time step
        self.target.time = self.target.time + start.time
        return super().compute(start)

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        return 0.0, 0.0
