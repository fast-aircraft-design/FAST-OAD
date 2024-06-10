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

from copy import copy
from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd
from scipy.constants import foot, g

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.exceptions import FastFlightSegmentIncompleteFlightPoint
from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.segments.time_step_base import AbstractManualThrustSegment
from fastoad.models.performances.mission.util import get_closest_flight_level


@RegisterSegment("altitude_change")
@dataclass
class AltitudeChangeSegment(AbstractManualThrustSegment):
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

    #: Using this value will tell to target the altitude with max lift/drag ratio.
    OPTIMAL_ALTITUDE = "optimal_altitude"  # pylint: disable=invalid-name # used as constant

    #: Using this value will tell to target the nearest flight level to altitude
    #: with max lift/drag ratio.
    OPTIMAL_FLIGHT_LEVEL = "optimal_flight_level"  # pylint: disable=invalid-name # used as constant

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        if target.altitude is not None:
            if isinstance(target.altitude, str):
                # Target altitude will be modified along the process, so we keep track
                # of the original order in target CL, that is not used otherwise.
                target.CL = target.altitude  # pylint: disable=invalid-name
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
                target.CL = None
                self.interrupt_if_getting_further_from_target = True

        atm = self._get_atmosphere_point(start.altitude)
        if target.equivalent_airspeed == self.CONSTANT_VALUE:
            atm.equivalent_airspeed = start.equivalent_airspeed
            start.true_airspeed = atm.true_airspeed
        elif target.mach == self.CONSTANT_VALUE:
            atm.mach = start.mach
            start.true_airspeed = atm.true_airspeed

        return super().compute_from_start_to_target(start, target)

    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:
        current = flight_points[-1]

        # Max flight level is first priority
        max_authorized_altitude = self.maximum_flight_level * 100.0 * foot
        if current.altitude >= max_authorized_altitude:
            return max_authorized_altitude - current.altitude

        if target.CL:
            # Optimal altitude is based on a target Mach number, though target speed
            # may be specified as TAS or EAS. If so, Mach number has to be computed
            # for target altitude and speed.

            # First, as target speed is expected to be set to self.CONSTANT_VALUE for one
            # parameter. Let's get the real value from start point.
            target_speed = copy(target)
            for speed_param in ["true_airspeed", "equivalent_airspeed", "mach"]:
                if isinstance(getattr(target_speed, speed_param), str):
                    setattr(target_speed, speed_param, getattr(flight_points[0], speed_param))

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
            if target.CL == self.OPTIMAL_ALTITUDE:
                target.altitude = optimal_altitude
            else:  # target.CL == self.OPTIMAL_FLIGHT_LEVEL:
                target.altitude = get_closest_flight_level(optimal_altitude, up_direction=False)

        if target.altitude is not None:
            return target.altitude - current.altitude
        if target.true_airspeed and target.true_airspeed != self.CONSTANT_VALUE:
            return target.true_airspeed - current.true_airspeed
        if target.equivalent_airspeed and target.equivalent_airspeed != self.CONSTANT_VALUE:
            return target.equivalent_airspeed - current.equivalent_airspeed
        if target.mach is not None and target.mach != self.CONSTANT_VALUE:
            return target.mach - current.mach

        raise FastFlightSegmentIncompleteFlightPoint(
            "No valid target definition for altitude change."
        )

    def get_gamma_and_acceleration(self, flight_point: FlightPoint) -> Tuple[float, float]:
        gamma = (flight_point.thrust - flight_point.drag) / flight_point.mass / g
        return gamma, 0.0
