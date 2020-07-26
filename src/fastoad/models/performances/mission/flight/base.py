"""Base classes for flight computation."""
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

from typing import List, Union

import pandas as pd
from fastoad.base.flight_point import FlightPoint
from scipy.optimize import root_scalar

from ..base import AbstractFlightSequence, IFlightPart
from ..segments.cruise import CruiseSegment


class AbstractSimpleFlight(AbstractFlightSequence):
    """
    Computes a simple flight.

    The computed flight will be be made of:
        - any number of climb phases
        - one cruise segment
        - any number of descent phases.
    """

    def __init__(
        self,
        cruise_distance: float,
        climb_phases: List[AbstractFlightSequence],
        cruise_phase: CruiseSegment,
        descent_phases: List[AbstractFlightSequence],
    ):
        """

        :param cruise_distance:
        :param climb_phases:
        :param cruise_phase:
        :param descent_phases:
        """

        self.climb_phases = climb_phases
        self.cruise_segment = cruise_phase
        self.cruise_segment.target = FlightPoint(ground_distance=cruise_distance, mach="constant")
        self.descent_phases = descent_phases

    @property
    def cruise_distance(self):
        return self.cruise_segment.target

    @cruise_distance.setter
    def cruise_distance(self, cruise_distance):
        self.cruise_segment.target = FlightPoint(ground_distance=cruise_distance)

    @property
    def flight_sequence(self) -> List[Union[IFlightPart, str]]:
        return self.climb_phases + [self.cruise_segment] + self.descent_phases


class RangedFlight(IFlightPart):
    """
    Computes a flight so that it covers the specified distance.
    """

    def __init__(
        self, flight_definition: AbstractSimpleFlight, flight_distance: float,
    ):
        """
        Computes the flight and adjust the cruise distance to achieve the provided flight distance.

        :param flight_definition:
        :param flight_distance: in meters
        """
        self.flight_distance = flight_distance
        self.flight = flight_definition
        self.flight_points = None
        self.distance_accuracy = 0.5e3

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        def compute_flight(cruise_distance):
            self.flight.cruise_distance = cruise_distance
            self.flight_points = self.flight.compute_from(start)
            obtained_distance = (
                self.flight_points.iloc[-1].ground_distance
                - self.flight_points.iloc[0].ground_distance
            )
            return self.flight_distance - obtained_distance

        root_scalar(
            compute_flight,
            x0=self.flight_distance * 0.5,
            x1=self.flight_distance * 0.25,
            xtol=0.5e3,
            method="secant",
        )
        return self.flight_points
