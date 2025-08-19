"""Classes for acceleration/deceleration segments."""

from dataclasses import dataclass
from typing import List, Tuple

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.exceptions import FastFlightSegmentIncompleteFlightPoint
from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.segments.time_step_base import (
    AbstractLiftFromWeightSegment,
    AbstractManualThrustSegment,
)


@RegisterSegment("speed_change")
@dataclass
class SpeedChangeSegment(AbstractManualThrustSegment, AbstractLiftFromWeightSegment):
    """
    Computes a flight path segment where speed is modified with no change in altitude.

    The target must define a speed value among true_airspeed, equivalent_airspeed
    and mach.
    """

    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:
        if target.true_airspeed is not None:
            return target.true_airspeed - flight_points[-1].true_airspeed
        if target.equivalent_airspeed is not None:
            return target.equivalent_airspeed - flight_points[-1].equivalent_airspeed
        if target.calibrated_airspeed is not None:
            return target.calibrated_airspeed - flight_points[-1].calibrated_airspeed
        if target.mach is not None:
            return target.mach - flight_points[-1].mach

        raise FastFlightSegmentIncompleteFlightPoint(
            "No valid target definition for altitude change."
        )

    def get_gamma_and_acceleration(self, flight_point: FlightPoint) -> Tuple[float, float]:
        acceleration = (flight_point.thrust - flight_point.drag) / flight_point.mass
        return 0.0, acceleration
