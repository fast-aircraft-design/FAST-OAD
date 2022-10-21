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

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
from scipy.optimize import root_scalar

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.base import FlightSequence
from fastoad.models.performances.mission.routes import RangedRoute
from fastoad.models.performances.mission.segments.cruise import CruiseSegment


@dataclass
class Mission(FlightSequence):
    """
    Computes a whole mission.

    Allows to define a target fuel consumption for the whole mission.
    """

    #: If not None, the mission will adjust the first
    target_fuel_consumption: Optional[float] = None

    #: Accuracy on actual consumed fuel for the solver. In kg
    fuel_accuracy: float = 10.0

    _flight_points: Optional[pd.DataFrame] = field(init=False, default=None)
    _first_cruise_segment: Optional[CruiseSegment] = field(init=False, default=None)

    @property
    def consumed_fuel(self) -> Optional[float]:
        """Total consumed fuel for the whole mission (after launching :meth:`compute_from`)"""
        if self._flight_points is None:
            return None

        return self._flight_points.mass.iloc[0] - self._flight_points.mass.iloc[-1]

    @property
    def first_route(self) -> RangedRoute:
        """First route in the mission."""
        return self._get_first_route_in_sequence(self)

    def _get_first_route_in_sequence(self, flight_sequence: FlightSequence) -> RangedRoute:
        for part in flight_sequence:
            if isinstance(part, RangedRoute):
                return part
            if isinstance(part, FlightSequence):
                route = self._get_first_route_in_sequence(part)
                if route:
                    return route

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        if self.target_fuel_consumption is None:
            return super().compute_from(start)
        else:
            return self._solve_cruise_distance(start)

    def _solve_cruise_distance(self, start: FlightPoint) -> pd.DataFrame:
        """
        Adjusts cruise distance through a solver to have whole route that
        matches provided consumed fuel.
        """

        self.first_route.solve_distance = False
        input_cruise_distance = self.first_route.flight_distance

        root_scalar(
            self._compute_flight,
            args=(start,),
            x0=input_cruise_distance * 0.5,
            x1=input_cruise_distance * 1.0,
            xtol=self.fuel_accuracy,
            method="secant",
        )

        return self._flight_points

    def _compute_flight(self, cruise_distance, start: FlightPoint):
        """
        Computes flight for provided cruise distance

        :param cruise_distance:
        :param start:
        :return: difference between computed fuel and self.target_fuel_consumption
        """
        self.first_route.cruise_distance = cruise_distance
        self._flight_points = super().compute_from(start)
        return self.target_fuel_consumption - self.consumed_fuel
