"""Class for mission start point."""
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

from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import IPropulsion
from .base import FlightSegment
from ..exceptions import FastFlightSegmentIncompleteFlightPoint
from ..polar import Polar


@dataclass
class Start(FlightSegment, mission_file_keyword="start"):
    """
    Provides a starting point for a mission.

    :meth:`compute_from` will return only 1 flight points that matches the target.
    """

    #: Unused
    propulsion: IPropulsion = None

    #: Unused
    reference_area: float = 1.0

    #: Unused
    polar: Polar = None

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:

        self.target.name = self.name

        if self.target.mass is None:
            # If not setting the mass in the start point, the default value set in
            # mission component will be used.
            self.target.mass = start.mass

        try:
            self.complete_flight_point(self.target)
        except FastFlightSegmentIncompleteFlightPoint:
            self.target.true_airspeed = 0.0
            self.complete_flight_point(self.target)

        return pd.DataFrame([self.target])

    def get_gamma_and_acceleration(self, flight_point: FlightPoint) -> Tuple[float, float]:
        return 0.0, 0.0

    # As we overloaded self.compute_from(), next abstract method are not used.
    # We just need to implement them for Python to be happy.
    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:
        pass

    def compute_propulsion(self, flight_point: FlightPoint):
        pass
