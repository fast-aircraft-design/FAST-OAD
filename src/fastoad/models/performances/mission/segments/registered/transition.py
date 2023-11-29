"""Class for very simple transition in some flight phases."""
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

from copy import deepcopy
from dataclasses import dataclass

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.segments.base import AbstractFlightSegment, RegisterSegment


@RegisterSegment("transition")
@dataclass
class DummyTransitionSegment(AbstractFlightSegment):
    """
    Computes a transient flight part in a very quick and dummy way.

    :meth:`compute_from` will return only 2 or 3 flight points.

    The second flight point is the end of transition. Its parameters are equal to those provided
    in :attr:`~fastoad.models.performances.mission.segments.base.FlightSegment.target`.

    There is an exception if target does not specify any mass (i.e. self.target.mass == 0). Then
    the mass of the second flight point is the start mass multiplied by :attr:`mass_ratio`.

    If :attr:`reserve_mass_ratio` is non-zero, a third flight point is added, with parameters equal
    to flight_point(2), except for mass where:
        mass(2) - reserve_mass_ratio * mass(3) = mass(3).
    In different words, mass(3) would be the Zero Fuel Weight (ZFW) and reserve can be
    expressed as a percentage of ZFW.
    """

    #: The ratio (aircraft mass at END of segment)/(aircraft mass at START of segment)
    mass_ratio: float = 1.0

    #: The ratio (fuel mass)/(aircraft mass at END of segment) that will be consumed at end
    #: of segment.
    reserve_mass_ratio: float = 0.0

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        end = deepcopy(target)
        end.name = self.name

        if end.mass is None:
            self.consume_fuel(end, previous=start, mass_ratio=self.mass_ratio)
        else:
            end.consumed_fuel = start.consumed_fuel + start.mass - end.mass

        self.complete_flight_point_from(end, start)
        self.complete_flight_point(end)

        flight_points = [start, end]

        if self.reserve_mass_ratio > 0.0:
            reserve = deepcopy(end)
            reserve.mass = end.mass / (1.0 + self.reserve_mass_ratio)
            self.consume_fuel(
                reserve, previous=end, mass_ratio=1.0 / (1.0 + self.reserve_mass_ratio)
            )
            flight_points.append(reserve)

        return pd.DataFrame(flight_points)
