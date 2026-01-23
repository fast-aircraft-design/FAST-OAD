"""Classes for climb/descent segments with regulated thrust."""

#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2026 ONERA & ISAE-SUPAERO
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

from copy import copy
from dataclasses import dataclass, field

import pandas as pd
from scipy.constants import foot, g

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.exceptions import (
    FastFlightSegmentIncompleteFlightPointError,
)
from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.segments.time_step_base import (
    AbstractLiftFromWeightSegment,
    AbstractRegulatedThrustSegment,
)
from fastoad.models.performances.mission.util import get_closest_flight_level


@RegisterSegment("altitude_change")
@dataclass
class AltitudeChangeSegment(AbstractRegulatedThrustSegment, AbstractLiftFromWeightSegment):
    """
    Computes a flight path segment where altitude is modified with constant speed and imposed slope angle.
    As a result, the thrust is regulated

    .. note:: **Setting speed**

        Constant speed may be:

        - constant true airspeed (TAS)
        - constant equivalent airspeed (EAS)
        - constant Mach number

        Target should have :code:`"constant"` as definition for one parameter among
        :code:`true_airspeed`, :code:`equivalent_airspeed` or :code:`mach`.
        All computed flight points will use the corresponding **start** value.
        The two other speed values will be computed accordingly.

        If not "constant" parameter is set, constant TAS is assumed.

    .. note:: **Setting target**

        Target can be an altitude:

        - Target altitude can be a float value (in **meters**),

        As a regulated segment, the calculated thrust may be larger than the maximal thrust (thrust_rate>1)
        In this case, the segment falls back on to a non-regulated altitude change segment

    """

    time_step: float = 2.0

    # The target slope angle in radian
    slope_angle: float = 0.05

    def __post_init__(self):
        super().__post_init__()
        self._slope_angle = self.slope_angle

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        # Use normal settings
        self.interrupt_if_getting_further_from_target = True

        # Need to add a specific mecanism to fall back on to manual thrust segment if thrust_rate > 1
        flight_points = super().compute_from_start_to_target(FlightPoint, target)

        # Check that the thrust rate of the last flight point
        if flight_points[-1].thrust_rate > 1.0:
            del flight_points[-1]
            start = flight_points[-1]
            # We are asking for a too high thrust rate, falling back on a manual thrust segment
            climb_segment = AltitudeChangeSegment(
                target=deepcopy(target),  # deepcopy needed because altitude may be modified.
                propulsion=self.propulsion,
                reference_area=self.reference_area,
                polar=self.polar,
                name=self.name,
                engine_setting=self.engine_setting,
            )

            climb_points = climb_segment.compute_from(start)
            flight_points = pd.concat([flight_points, climb_points]).reset_index(drop=True)

        return flight_points

    def get_distance_to_target(
        self, flight_points: list[FlightPoint], target: FlightPoint
    ) -> float:
        current = flight_points[-1]

        distance_to_target = None

        if target.altitude is not None:
            distance_to_target = target.altitude - current.altitude

        if distance_to_target is None:
            raise FastFlightSegmentIncompleteFlightPointError(
                "No valid target definition for altitude change."
            )

        return distance_to_target
