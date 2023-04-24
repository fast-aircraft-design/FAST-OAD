"""Class for specifying input mass at "any" point in the mission."""
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

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.segments.base import AbstractFlightSegment, RegisterSegment


@RegisterSegment("mass_input")
@dataclass
class MassTargetSegment(AbstractFlightSegment):
    """
    Class that simply sets a target mass.

    :meth:`compute_from` returns a 1-row dataframe that is the start point with mass
    set to provided target mass.

    class:`~fastoad.models.performances.mission.base.FlightSequence` ensures that
    mass is consistent for segments prior to this one.
    """

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        start.mass = target.mass
        self.complete_flight_point(start)
        return pd.DataFrame([start])
