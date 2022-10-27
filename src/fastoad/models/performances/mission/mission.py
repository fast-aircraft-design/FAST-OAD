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

from copy import deepcopy
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

        return (
            self._flight_points.mass.iloc[0]
            - self._flight_points.mass.iloc[-1]
            + self.get_reserve_fuel()
        )

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
            return self._compute_from(start)
        else:
            return self._solve_cruise_distance(start)

    def _compute_from(self, start: FlightPoint) -> pd.DataFrame:
        flight_points = super().compute_from(start)
        flight_points.name.loc[flight_points.name.isnull()] = ""

        if self.reserve_ratio > 0.0:
            if self.reserve_base_route_name is None:
                base_route_name = self.first_route.name
            else:
                base_route_name = self.reserve_base_route_name

            reserve_fuel = self.reserve_ratio * self._get_consumed_mass_in_route(base_route_name)
            reserve_points = pd.DataFrame(
                [
                    deepcopy(flight_points.iloc[-1]),
                    deepcopy(flight_points.iloc[-1]),
                ]
            )

            # We are not using -= here because it would operate last_flight_point.mass can be
            # an array. The operator would operate element-wise and would modify the original
            # flight point, despite the deepcopy.
            reserve_points.mass.iloc[-1] = reserve_points.mass.iloc[0] - reserve_fuel
            reserve_points["name"] = f"{self.name}:reserve"

            self.part_flight_points.append(reserve_points)

        return flight_points

    def _get_consumed_mass_in_route(self, route_name: str) -> float:
        route = [part for part in self if part.name == route_name][0]
        route_idx = self.index(route)
        route_points = self.part_flight_points[route_idx]
        return route_points.mass.iloc[0] - route_points.mass.iloc[-1]

    def get_reserve_fuel(self):
        if not self.reserve_ratio:
            return 0.0

        reserve_points = self.part_flight_points[-1]

        return reserve_points.iloc[0].mass - reserve_points.iloc[-1].mass

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
        self._flight_points = self._compute_from(start)
        return self.target_fuel_consumption - self.consumed_fuel
