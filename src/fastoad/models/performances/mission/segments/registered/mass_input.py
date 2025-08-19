"""Class for specifying input mass at "any" point in the mission."""

from dataclasses import dataclass

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.segments.base import AbstractFlightSegment, RegisterSegment


@RegisterSegment("mass_input")
@dataclass
class MassTargetSegment(AbstractFlightSegment):
    """
    Class that simply sets a target mass.

    :meth:`compute_from` returns a 1-row dataframe that is the start point with mass
    set to provided target mass.

    class:`~fastoad.models.performances.mission.base.FlightSequence` ensures that
    mass is consistent for segments prior to this one.
    """

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        start.mass = target.mass
        self.complete_flight_point(start)
        return pd.DataFrame([start])
