"""Classes for Taxi sequences."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from fastoad.models.performances.mission.segments.base import FixedDurationSegment
from .base import ManualThrustSegment
from ..polar import Polar


@dataclass
class TaxiSegment(ManualThrustSegment, FixedDurationSegment):
    """
    Class for computing Taxi phases.

    Taxi phase has a target duration (target.time should be provided) and is at
    constant altitude, speed and thrust rate.
    """

    polar: Polar = None
    reference_area: float = 1.0
    time_step: float = 60.0

    def _get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        return 0.0, 0.0
