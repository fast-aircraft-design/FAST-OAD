"""Definition of aircraft mission."""

#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
from scipy.optimize import root_scalar

from fastoad.model_base import FlightPoint
from .base import FlightSequence
from .routes import RangedRoute
from .segments.registered.cruise import CruiseSegment


@dataclass
class Mission(FlightSequence):
    """
    Computes a whole mission.

    Allows to define a target fuel consumption for the whole mission.
    """

    #: If not None, the mission will adjust the first
    target_fuel_consumption: Optional[float] = None

    reserve_ratio: Optional[float] = 0.0
    reserve_base_route_name: Optional[str] = None

    #: Accuracy on actual consumed fuel for the solver. In kg
    fuel_accuracy: float = 10.0

    _flight_points: Optional[pd.DataFrame] = field(init=False, default=None)
    _first_cruise_segment: Optional[CruiseSegment] = field(init=False, default=None)

    @property
    def consumed_fuel(self) -> Optional[float]:
        """Total consumed fuel for the whole mission (after launching :meth:`compute_from`)"""
        if self._flight_points is None:
            return None

        return self._flight_points.iloc[-1].consumed_fuel + self.get_reserve_fuel()

    @property
    def first_route(self) -> RangedRoute:
        """First route in the mission."""
        return self._get_first_route_in_sequence(self)

    def _get_first_route_in_sequence(
        self, flight_sequence: FlightSequence
    ) -> Optional[RangedRoute]:
        for part in flight_sequence:
            if isinstance(part, RangedRoute):
                return part
            if isinstance(part, FlightSequence):
                route = self._get_first_route_in_sequence(part)
                if route:
                    return route

        return None

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        if self.target_fuel_consumption is None:
            self._flight_points = super().compute_from(start)
            self._flight_points.loc[self._flight_points.name.isnull()].name = ""
            self._compute_reserve(self._flight_points)
        else:
            self._solve_cruise_distance(start)

        return self._flight_points

    def get_reserve_fuel(self):
        """:returns: the fuel quantity for reserve, obtained after mission computation."""
        if not self.reserve_ratio or not self.part_flight_points:
            return 0.0

        reserve_points = self.part_flight_points[-1]

        return reserve_points.iloc[0].mass - reserve_points.iloc[-1].mass

    def _get_consumed_mass_in_route(self, route_name: str) -> float:
        route = [part for part in self if part.name == route_name][0]
        route_idx = self.index(route)
        route_points = self.part_flight_points[route_idx]
        return route_points.mass.iloc[0] - route_points.mass.iloc[-1]

    def _compute_reserve(self, flight_points):
        """Adds a "reserve part" in self.part_flight_points."""
        if self.reserve_ratio > 0.0:
            if self.reserve_base_route_name is None:
                base_route_name = self.first_route.name
            else:
                base_route_name = self.reserve_base_route_name

            reserve_fuel = self.reserve_ratio * self._get_consumed_mass_in_route(base_route_name)
            last_flight_point = flight_points.iloc[-1]

            after_reserve_point = deepcopy(last_flight_point)
            after_reserve_point.mass = last_flight_point.mass - reserve_fuel

            reserve_points = pd.DataFrame([last_flight_point, after_reserve_point])
            reserve_points["name"] = f"{self.name}:reserve"

            self.part_flight_points.append(reserve_points)

    def _solve_cruise_distance(self, start: FlightPoint) -> pd.DataFrame:
        """
        Adjusts cruise distance through a solver to have whole route that
        matches provided consumed fuel.
        """

        if self.target_fuel_consumption == 0.0:
            start.name = self.name
            self._flight_points = pd.DataFrame([start, start])
        else:
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
        flight_points = super().compute_from(start)
        flight_points.loc[flight_points.name.isnull()].name = ""
        self._compute_reserve(flight_points)
        self._flight_points = flight_points
        return self.target_fuel_consumption - self.consumed_fuel
