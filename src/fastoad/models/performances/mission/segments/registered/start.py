"""Class for mission start point."""

from dataclasses import dataclass

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.exceptions import FastFlightSegmentIncompleteFlightPoint
from fastoad.models.performances.mission.segments.base import AbstractFlightSegment, RegisterSegment


@RegisterSegment("start")
@dataclass
class Start(AbstractFlightSegment):
    """
    Provides a starting point for a mission.

    :meth:`compute_from` will return only 1 flight points that matches the target.
    """

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        target.name = self.name

        if target.mass is None:
            # If not setting the mass in the start point, the default value set in
            # mission component will be used.
            target.mass = start.mass

        try:
            self.complete_flight_point(target)
        except FastFlightSegmentIncompleteFlightPoint:
            target.true_airspeed = 0.0
            self.complete_flight_point(target)

        return pd.DataFrame([target])
