"""Class for mission start point."""
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
from fastoad.models.performances.mission.exceptions import FastFlightSegmentIncompleteFlightPoint
from fastoad.models.performances.mission.segments.base import AbstractFlightSegment, RegisterSegment


@RegisterSegment("start")
@dataclass
class Start(AbstractFlightSegment):
    """
    Provides a starting point for a mission.

    :meth:`compute_from` will return only 1 flight points that matches the target.
    """

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        target.name = self.name

        if target.mass is None:
            # If not setting the mass in the start point, the default value set in
            # mission component will be used.
            target.mass = start.mass

        try:
            self.complete_flight_point(target)
        except FastFlightSegmentIncompleteFlightPoint:
            target.true_airspeed = 0.0
            self.complete_flight_point(target)

        return pd.DataFrame([target])
