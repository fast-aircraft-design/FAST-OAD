"""Classes for Taxi sequences."""

from dataclasses import dataclass
from typing import Tuple

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.polar import Polar
from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.segments.time_step_base import (
    AbstractFixedDurationSegment,
    AbstractLiftFromAoASegment,
    AbstractManualThrustSegment,
)


@RegisterSegment("taxi")
@dataclass
class TaxiSegment(
    AbstractManualThrustSegment, AbstractFixedDurationSegment, AbstractLiftFromAoASegment
):  # noqa: F821
    """
    Class for computing Taxi phases.

    Taxi phase has a target duration (target.time should be provided) and is at
    constant altitude, speed and thrust rate.
    """

    polar: Polar = None
    reference_area: float = 1.0
    time_step: float = 60.0
    true_airspeed: float = 0.0

    def get_gamma_and_acceleration(self, flight_point: FlightPoint) -> Tuple[float, float]:
        return 0.0, 0.0

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        start.mach = None
        start.equivalent_airspeed = None
        start.true_airspeed = self.true_airspeed
        self.complete_flight_point(start)

        return super().compute_from_start_to_target(start, target)
