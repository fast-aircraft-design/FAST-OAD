"""Base classes for mission computation."""
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

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import BaseDataClass


@dataclass
class IFlightPart(ABC, BaseDataClass):
    """
    Base class for all flight parts.
    """

    name: str = ""
    target: FlightPoint = field(init=False, default=None)

    @abstractmethod
    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        """
        Computes a flight sequence from provided start point.

        :param start: the initial flight point, defined for `altitude`, `mass` and speed
                      (`true_airspeed`, `equivalent_airspeed` or `mach`). Can also be
                      defined for `time` and/or `ground_distance`.
        :return: a pandas DataFrame where column names match fields of
                 :class:`~fastoad.model_base.flight_point.FlightPoint`
        """


@dataclass
class FlightSequence(IFlightPart):
    """
    Defines and computes a flight sequence.
    """

    #: List of IFlightPart instances that should be run sequentially.
    flight_sequence: List[IFlightPart] = field(default_factory=list)

    #: Consumed mass between sequence start and target mass, if any defined
    consumed_mass_before_input_weight: float = field(default=0.0, init=False)

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        parts = []
        part_start = deepcopy(start)
        part_start.scalarize()

        self.consumed_mass_before_input_weight = 0.0
        consumed_mass = 0.0
        for part in self.flight_sequence:
            # This check has to be done first because relative target parameters
            # will be made absolute during compute_from()
            part_has_target_mass = not (part.target.mass is None or part.target.is_relative("mass"))

            flight_points = part.compute_from(part_start)

            consumed_mass += flight_points.iloc[0].mass - flight_points.iloc[-1].mass

            if isinstance(part, FlightSequence):
                self.consumed_mass_before_input_weight += part.consumed_mass_before_input_weight

            # If a part has a target mass, computed mass of all previous part must be
            # offset so this target will be reached.
            # (mass consumption of previous parts is assumed independent of aircraft mass)
            if part_has_target_mass:
                mass_offset = flight_points.iloc[0].mass - part_start.mass
                for previous_flight_points in parts:
                    previous_flight_points.mass += mass_offset
                self.consumed_mass_before_input_weight = float(consumed_mass)

            if len(parts) > 0 and len(flight_points) > 1:
                # First point of the segment is omitted, as it is the last of previous segment.
                #
                # But sometimes (especially in the case of simplistic segments), the new first
                # point may contain more information than the previous last one. In such case,
                # it is interesting to complete the previous last one.
                last_flight_points = parts[-1]
                last_index = last_flight_points.index[-1]
                for name in flight_points.columns:
                    value = last_flight_points.loc[last_index, name]
                    if not value:
                        last_flight_points.loc[last_index, name] = flight_points.loc[0, name]

                parts.append(flight_points.iloc[1:])

            else:
                # But it is kept if the computed segment is the first one.
                parts.append(flight_points)

            part_start = FlightPoint.create(flight_points.iloc[-1])
            part_start.scalarize()

        if parts:
            return pd.concat(parts).reset_index(drop=True)

    @property
    def target(self) -> Optional[FlightPoint]:
        """Target of the last element of current sequence."""
        if len(self.flight_sequence) > 0:
            return self.flight_sequence[-1].target

        return None
