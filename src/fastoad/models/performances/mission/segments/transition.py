"""Class for very simple transition in some flight phases."""
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

from copy import deepcopy
from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import IPropulsion
from fastoad.models.performances.mission.polar import Polar
from fastoad.models.performances.mission.segments.base import FlightSegment


@dataclass
class DummyTransitionSegment(FlightSegment, mission_file_keyword="transition"):
    """
    Computes a transient flight part in a very quick and dummy way.

    :meth:`compute_from` will return only 2 or 3 flight points.

    The second flight point is the end of transition and its mass is the start mass
    multiplied by :attr:`mass_ratio`. Other parameters are equal to those provided in
    :attr:`~fastoad.models.performances.mission.segments.base.FlightSegment.target`.

    If :attr:`reserve_mass_ratio` is non-zero, a third flight point, with parameters equal
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

    #: Unused
    propulsion: IPropulsion = None

    #: Unused
    reference_area: float = 1.0

    #: Unused
    polar: Polar = None

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:

        self.complete_flight_point(start)
        end = deepcopy(start)

        end.mass = start.mass * self.mass_ratio
        end.altitude = self.target.altitude
        end.ground_distance = start.ground_distance + self.target.ground_distance
        end.mach = self.target.mach
        end.true_airspeed = self.target.true_airspeed
        end.equivalent_airspeed = self.target.equivalent_airspeed
        end.name = self.name
        self.complete_flight_point(end)

        flight_points = [start, end]

        if self.reserve_mass_ratio > 0.0:
            reserve = deepcopy(end)
            reserve.mass = end.mass / (1.0 + self.reserve_mass_ratio)
            flight_points.append(reserve)

        return pd.DataFrame(flight_points)

    def _get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        return 0.0, 0.0

    # As we overloaded self.compute_from(), next abstract method are not used.
    # We just need to implement them for Python to be happy.
    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> float:
        pass

    def _compute_propulsion(self, flight_point: FlightPoint):
        pass
