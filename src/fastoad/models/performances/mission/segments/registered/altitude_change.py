"""Classes for climb/descent segments."""

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

import logging
from copy import copy, deepcopy
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.constants import foot, g

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.exceptions import (
    FastFlightSegmentIncompleteFlightPointError,
)
from fastoad.models.performances.mission.segments.constants import ThrustRateOutOfBound
from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.segments.time_step_base import (
    AbstractLiftFromWeightSegment,
    AbstractManualThrustSegment,
    AbstractRegulatedThrustSegment,
)
from fastoad.models.performances.mission.util import get_closest_flight_level

_LOGGER = logging.getLogger(__name__)  # Logger for this module



@dataclass
class BaseAltitudeChange(AbstractLiftFromWeightSegment):
    """
    Computes a flight path segment where altitude is modified with constant speed.

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

        Target can be an altitude, or a speed:

        - Target altitude can be a float value (in **meters**), or can be set to:

            - :attr:`OPTIMAL_ALTITUDE`: in that case, the target altitude will be the altitude
              where maximum lift/drag ratio is achieved for target speed, depending on current mass.
            - :attr:`OPTIMAL_FLIGHT_LEVEL`: same as above, except that altitude will be rounded to
              the nearest flight level (multiple of 100 feet).

        - For a speed target, as explained above, one value  TAS, EAS or Mach must be
          :code:`"constant"`. One of the two other ones can be set as target.

        In any case, the achieved value will be capped so it respects
        :attr:`maximum_flight_level`.

    """

    time_step: float = 2.0

    #: The maximum allowed flight level (i.e. multiple of 100 feet).
    maximum_flight_level: float = 500.0

    #: To keep track of originally instructed target (used for "optimal_altitude" and so on)
    _original_target_altitude: str | None = field(default=None, init=False)

    #: Using this value will tell to target the altitude with max lift/drag ratio.
    OPTIMAL_ALTITUDE = "optimal_altitude"  # used as constant

    #: Using this value will tell to target the nearest flight level to altitude
    #: with max lift/drag ratio.
    OPTIMAL_FLIGHT_LEVEL = "optimal_flight_level"  # used as constant

    def _handle_target_settings(self, target: FlightPoint, start: FlightPoint) -> None:
        if target.altitude is not None:
            if isinstance(target.altitude, str):
                # Target altitude will be modified along the process, so we keep track
                # of the original order.
                self._original_target_altitude = target.altitude

                # let's put a numerical, negative value in target.altitude to
                # ensure there will be no problem in self.get_distance_to_target()
                target.altitude = -1000.0
                if self.get_distance_to_target([start], target) > 0:
                    # If target is a CL and distance to target is positive, then
                    # the target CL might be achieved even if it gets further
                    # at some time, because of the mass loss.
                    # Then it is better to deactivate this safeguard.
                    self.interrupt_if_getting_further_from_target = False
            else:
                # Target altitude is fixed, back to original settings (in case
                # this instance is used more than once)
                self._original_target_altitude = None
                self.interrupt_if_getting_further_from_target = True

        atm = self._get_atmosphere_point(start.altitude)
        if target.equivalent_airspeed == self.constant_value_name:
            atm.equivalent_airspeed = start.equivalent_airspeed
            start.true_airspeed = atm.true_airspeed
        elif target.mach == self.constant_value_name:
            atm.mach = start.mach
            start.true_airspeed = atm.true_airspeed

        if self.maximum_CL is not None:
            if start.CL is not None and start.CL > self.maximum_CL:  # noqa: SIM300 False positive
                # If CL of the starting point is above the max CL, we stop the climb/descent
                _LOGGER.warning(
                    'The first point in a segment of "%s" has a CL = %.2f > maximum_CL = %.2f. '
                    'Skipping "altitude_change" segment.',
                    self.name,
                    start.CL,
                    self.maximum_CL,
                )
                target.CL = self.maximum_CL  # to avoid any processing

    def get_distance_to_target(
        self, flight_points: list[FlightPoint], target: FlightPoint
    ) -> float:
        current = flight_points[-1]

        distance_to_target = None

        # Max flight level is first priority
        max_authorized_altitude = self.maximum_flight_level * 100.0 * foot
        if current.altitude >= max_authorized_altitude:
            distance_to_target = max_authorized_altitude - current.altitude

        # Max CL is second priority, if it is defined
        elif isinstance(target.CL, float) or (
            isinstance(self.maximum_CL, float) and self.maximum_CL < current.CL
        ):
            distance_to_target = target.CL - current.CL

        else:
            if self._original_target_altitude:
                self._manage_optimal_altitude(current, flight_points[0], target)

            if target.altitude is not None:
                distance_to_target = target.altitude - current.altitude
            elif target.true_airspeed and target.true_airspeed != self.constant_value_name:
                distance_to_target = target.true_airspeed - current.true_airspeed
            elif (
                target.equivalent_airspeed
                and target.equivalent_airspeed != self.constant_value_name
            ):
                distance_to_target = target.equivalent_airspeed - current.equivalent_airspeed
            elif target.mach is not None and target.mach != self.constant_value_name:
                distance_to_target = target.mach - current.mach

        if distance_to_target is None:
            raise FastFlightSegmentIncompleteFlightPointError(
                "No valid target definition for altitude change."
            )
        return distance_to_target

    def _manage_optimal_altitude(
        self, current: FlightPoint, start: FlightPoint, target: FlightPoint
    ) -> None:
        # Optimal altitude is based on a target Mach number, though target speed
        # may be specified as TAS or EAS. If so, Mach number has to be computed
        # for target altitude and speed.
        # First, as target speed is expected to be set to self.constant_value_name for one
        # parameter. Let's get the real value from start point.
        target_speed = copy(target)
        for speed_param in ["true_airspeed", "equivalent_airspeed", "mach"]:
            if isinstance(getattr(target_speed, speed_param), str):
                setattr(target_speed, speed_param, getattr(start, speed_param))
        # Now, let's compute target Mach number
        atm = self._get_atmosphere_point(max(target.altitude, current.altitude))
        if target_speed.equivalent_airspeed:
            atm.equivalent_airspeed = target_speed.equivalent_airspeed
            target_speed.true_airspeed = atm.true_airspeed
        if target_speed.true_airspeed:
            atm.true_airspeed = target_speed.true_airspeed
            target_speed.mach = atm.mach
        # Now we compute optimal altitude
        optimal_altitude = self._get_optimal_altitude(
            current.mass, target_speed.mach, current.altitude
        )
        if self._original_target_altitude == self.OPTIMAL_ALTITUDE:
            target.altitude = optimal_altitude
        else:  # self._original_target_altitude == self.OPTIMAL_FLIGHT_LEVEL:
            target.altitude = get_closest_flight_level(optimal_altitude, up_direction=False)


@RegisterSegment("altitude_change")
@dataclass
class AltitudeChangeSegment(BaseAltitudeChange, AbstractManualThrustSegment):
    """

    Computes a flight path segment where altitude is modified with constant speed.

     .. note:: **Thrust rate**

     This segment requires the thrust_rate to determine the slope angle.

    """

    def get_gamma_and_acceleration(self, flight_point: FlightPoint) -> tuple[float, float]:
        gamma = (flight_point.thrust - flight_point.drag) / flight_point.mass / g
        return gamma, 0.0

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        self._handle_target_settings(target, start)

        return super().compute_from_start_to_target(start, target)


@RegisterSegment("regulated_altitude_change")
@dataclass
class RegulatedAltitudeChangeSegment(BaseAltitudeChange, AbstractRegulatedThrustSegment):
    """

    Computes a flight path segment where altitude is modified with constant speed.

     .. note:: **Thrust rate**

     This segment determines the thrust rate according to the provided slope angle.

    """

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:

        self._handle_target_settings(target, start)

        # Compute the segment with no limitation on thrust_rate
        flight_points = super().compute_from_start_to_target(start, target)

        # Adjust according to the desired behaviour
        if self.thrust_rate_out_of_bound == ThrustRateOutOfBound.LIMIT.value:
            # Check for out of bound thrust rate and switch to manual thrust segment instead

            if np.any(flight_points.thrust_rate > self.upper_thrust_rate_limit):
                # We have a thrust rate too high, likely a climb phase,
                # thrust rate forced to self.upper_thrust_rate_limit

                # We use the last FlightPoint where thrust rate is < self.upper_thrust_rate_limit as a starting point.
                idx = np.argwhere(flight_points.thrust_rate > self.upper_thrust_rate_limit)
                i0 = int(idx[0, 0])
                if i0 == 0:
                    # Handle first point of segment being already at thrust rate > self.upper_thrust_rate_limit
                    start = FlightPoint.create(flight_points.iloc[i0])
                    # We drop the whole regulated segment and replace it by a manual one
                    flight_points.drop(flight_points.index, inplace=True)
                else:
                    start = FlightPoint.create(flight_points.iloc[i0 - 1])
                    flight_points.drop(
                        flight_points.loc[
                            flight_points.thrust_rate > self.upper_thrust_rate_limit
                        ].index,
                        inplace=True,
                    )

                start.thrust_is_regulated = False

                climb_segment = AltitudeChangeSegment(
                    target=deepcopy(target),  # deepcopy needed because altitude may be modified.
                    propulsion=self.propulsion,
                    reference_area=self.reference_area,
                    polar=self.polar,
                    name=self.name,
                    engine_setting=self.engine_setting,
                    thrust_rate=self.upper_thrust_rate_limit,
                    time_step=self.time_step,
                )

                non_regulated_climb_points = climb_segment.compute_from(start)
                flight_points = pd.concat([flight_points, non_regulated_climb_points]).reset_index(
                    drop=True
                )
                _LOGGER.info(
                    "Thrust rate limitation reached in regulated altitude change segment '%s',"
                    "cannot satisfy slope angle,"
                    "falling back on normal altitude change with constant thrust_rate=%.2f",
                    self.name,
                    self.upper_thrust_rate_limit,
                )

            elif np.any(flight_points.thrust_rate < self.lower_thrust_rate_limit):
                # We have a too low thrust rate, likely a descent phase,
                # thrust rate forced to self.lower_thrust_rate_limit

                # We use the last FlightPoint where thrust rate is < self.lower_thrust_rate_limit as a starting point.
                idx = np.argwhere(flight_points.thrust_rate < self.lower_thrust_rate_limit)
                i0 = int(idx[0, 0])
                if i0 == 0:
                    # Handle first point of segment being already at thrust rate < self.lower_thrust_rate_limit
                    start = FlightPoint.create(flight_points.iloc[i0])
                else:
                    start = FlightPoint.create(flight_points.iloc[i0 - 1])

                start.thrust_rate_is_regulated = False
                flight_points.drop(
                    flight_points.loc[
                        flight_points.thrust_rate < self.lower_thrust_rate_limit
                    ].index,
                    inplace=True,
                )

                climb_segment = AltitudeChangeSegment(
                    target=deepcopy(target),  # deepcopy needed because altitude may be modified.
                    propulsion=self.propulsion,
                    reference_area=self.reference_area,
                    polar=self.polar,
                    name=self.name,
                    engine_setting=self.engine_setting,
                    thrust_rate=self.lower_thrust_rate_limit,
                    time_step=self.time_step,
                )

                non_regulated_climb_points = climb_segment.compute_from(start)
                flight_points = pd.concat([flight_points, non_regulated_climb_points]).reset_index(
                    drop=True
                )

                _LOGGER.info(
                    "Thrust rate limitation reached in regulated altitude change segment '%s',"
                    "cannot satisfy slope angle,"
                    "falling back on normal altitude change with constant thrust_rate=%.2f",
                    self.name,
                    self.lower_thrust_rate_limit,
                )

            return flight_points

        elif self.thrust_rate_out_of_bound == ThrustRateOutOfBound.EXTRAPOLATE.value:
            # Do nothing, output the flightpoints with thrust rate out of bounds
            return flight_points

        # Raise a Value error
        raise ValueError(
            f"The value of option 'thrust_rate_out_of_bound' in regulated_altitude_change is invalid. "
            f"It must be one of {[member.value for member in ThrustRateOutOfBound]}"
        )
