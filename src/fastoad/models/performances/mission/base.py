"""Base classes for mission computation."""
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

from abc import ABC, abstractmethod
from typing import List, Union

import pandas as pd
from fastoad.base.flight_point import FlightPoint
from fastoad.models.performances.mission.polar import Polar
from fastoad.models.propulsion import IPropulsion


class IFlightPart(ABC):
    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        """
        Computes a flight sequence from provided start point.

        :param start: the initial flight point, defined for `altitude`, `mass` and speed
                      (`true_airspeed`, `equivalent_airspeed` or `mach`). Can also be
                      defined for `time` and/or `ground_distance`.
        :return: a pandas DataFrame where columns names match :attr:`FlightPoint.labels`
        """


class AbstractFlightSequence(IFlightPart):
    """
    Defines and computes a flight sequence.
    """

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        segments = []
        segment_start = start
        for segment_calculator in self.flight_sequence:
            flight_points = segment_calculator.compute_from(segment_start)
            if len(segments) > 0:
                # First point of the segment is omitted, as it is the
                # last of previous segment.
                if len(flight_points) > 1:
                    segments.append(flight_points.iloc[1:])
            else:
                # But it is kept if the computed segment is the first one.
                segments.append(flight_points)

            segment_start = FlightPoint(flight_points.iloc[-1])

        if segments:
            return pd.concat(segments).reset_index(drop=True)

    @property
    @abstractmethod
    def flight_sequence(self) -> List[Union[IFlightPart, str]]:
        """
        Defines the sequence as used in :meth:`compute_from`.

        :return: the list of IFlightPart instances for the mission.
        """


class AbstractManualThrustFlightPhase(AbstractFlightSequence, ABC):
    """
    Base class for climb and descent phases.
    """

    def __init__(
        self,
        *,
        propulsion: IPropulsion,
        reference_area: float,
        polar: Polar,
        thrust_rate: float = 1.0,
        name="",
        time_step=None,
    ):
        """
        Initialization is done only with keyword arguments.

        :param propulsion:
        :param reference_area:
        :param polar:
        :param thrust_rate:
        :param time_step: if provided, this time step will be applied for all segments.
        """

        self.segment_kwargs = {
            "propulsion": propulsion,
            "reference_area": reference_area,
            "polar": polar,
            "thrust_rate": thrust_rate,
            "name": name,
            "time_step": time_step,
        }
