"""Class for very simple transition in some flight phases."""

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

    #: If False, the mass variation during the segment is not considered as a fuel consumption.
    #:  (True by default
    fuel_is_consumed: bool = True

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        end = deepcopy(target)
        end.name = self.name
        end.consumed_fuel = start.consumed_fuel
        if end.mass is None:
            self.consume_fuel(end, previous=start, mass_ratio=self.mass_ratio)
        elif self.fuel_is_consumed:
            end.consumed_fuel += start.mass - end.mass

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
