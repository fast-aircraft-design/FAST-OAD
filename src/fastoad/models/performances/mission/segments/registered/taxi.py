"""Classes for Taxi sequences."""
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

from dataclasses import dataclass
from typing import Tuple

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.polar import Polar
from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.segments.time_step_base import (
    AbstractFixedDurationSegment,
    AbstractManualThrustSegment,
)


@RegisterSegment("taxi")
@dataclass
class TaxiSegment(AbstractManualThrustSegment, AbstractFixedDurationSegment):
    """
    Class for computing Taxi phases.

    Taxi phase has a target duration (target.time should be provided) and is at
    constant altitude, speed and thrust rate.
    """

    polar: Polar = None
    reference_area: float = 1.0
    time_step: float = 60.0
    true_airspeed: float = 0.0

    def get_gamma_and_acceleration(self, flight_point: FlightPoint) -> Tuple[float, float]:
        return 0.0, 0.0

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        start.mach = None
        start.equivalent_airspeed = None
        start.true_airspeed = self.true_airspeed
        self.complete_flight_point(start)

        return super().compute_from_start_to_target(start, target)
