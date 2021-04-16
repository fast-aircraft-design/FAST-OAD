"""Base classes for mission computation."""
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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

import pandas as pd

from fastoad.model_base import FlightPoint


class IFlightPart(ABC):
    def __init__(self):
        self.name = ""

    @abstractmethod
    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        """
        Computes a flight sequence from provided start point.

        :param start: the initial flight point, defined for `altitude`, `mass` and speed
                      (`true_airspeed`, `equivalent_airspeed` or `mach`). Can also be
                      defined for `time` and/or `ground_distance`.
        :return: a pandas DataFrame where columns names match fields of
                 :class:`~fastoad.model_base.flight_point.FlightPoint`
        """


@dataclass
class FlightSequence(IFlightPart):
    """
    Defines and computes a flight sequence.
    """

    def __post_init__(self):
        self._flight_sequence = []

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        parts = []
        part_start = start
        for part in self.flight_sequence:
            flight_points = part.compute_from(part_start)
            if len(parts) > 0:
                # First point of the segment is omitted, as it is the
                # last of previous segment.
                if len(flight_points) > 1:
                    parts.append(flight_points.iloc[1:])
            else:
                # But it is kept if the computed segment is the first one.
                parts.append(flight_points)

            part_start = FlightPoint.create(flight_points.iloc[-1])

        if parts:
            return pd.concat(parts).reset_index(drop=True)

    @property
    def flight_sequence(self) -> List[IFlightPart]:
        """List of IFlightPart instances that should be run sequentially."""
        return self._flight_sequence
