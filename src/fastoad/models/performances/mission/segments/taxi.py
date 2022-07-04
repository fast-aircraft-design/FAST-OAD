"""Classes for Taxi sequences."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

from copy import deepcopy
from dataclasses import dataclass
from typing import Tuple

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.segments.base import FixedDurationSegment
from .base import ManualThrustSegment
from ..polar import Polar


@dataclass
class TaxiSegment(
    ManualThrustSegment,
    FixedDurationSegment,
    mission_file_keyword="taxi",
    attribute_units=dict(true_airspeed="m/s"),
):
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

    def _compute_from(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        new_start = deepcopy(start)
        if target.mass:
            new_start.mass = target.mass
        new_start.mach = None
        new_start.equivalent_airspeed = None
        new_start.true_airspeed = self.true_airspeed

        flight_points = super()._compute_from(new_start, target)

        if target.mass:
            consumed_fuel = new_start.mass - flight_points.mass.iloc[-1]
            flight_points.mass += consumed_fuel

        return flight_points
