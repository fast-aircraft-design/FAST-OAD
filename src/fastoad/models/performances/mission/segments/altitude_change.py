"""Classes for climb/descent segments."""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
from typing import Tuple, List

import pandas as pd
from fastoad.utils.physics import AtmosphereSI
from scipy.constants import g

from .base import ManualThrustSegment
from ..flight_point import FlightPoint

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class AltitudeChangeSegment(ManualThrustSegment):
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

        Target can be an altitude, or a speed.

        Target altitude can be a float value (in **meters**), or can be set to
        :attr:`OPTIMAL_ALTITUDE`. In that last case, the target altitude will be the altitude where
        maximum lift/drag ratio is achieved for target speed, depending on current mass.

        For a speed target, as explained above, one value  TAS, EAS or Mach must be
        :code:`"constant"`. One of the two other ones can be set as target.

    .. warning::

        Whatever the above settings, if :attr:`cruise_mach` attribute is set, speed will always be
        limited so that Mach number keeps lower or equal to this value.

    """

    #: Using this value will tell to target the altitude with max lift/drag ratio.
    OPTIMAL_ALTITUDE = -10000.0

    def __init__(self, **kwargs):

        self._set_attribute_default("time_step", 2.0)
        super().__init__(**kwargs)

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        self.complete_flight_point(start)  # needed to ensure all speed values are computed.

        if self.target.altitude == self.OPTIMAL_ALTITUDE:
            self.target.CL = "optimal"

        atm = AtmosphereSI(start.altitude)
        if self.target.equivalent_airspeed == "constant":
            start.true_airspeed = atm.get_true_airspeed(start.equivalent_airspeed)
        elif self.target.mach == "constant":
            start.true_airspeed = start.mach * atm.speed_of_sound

        return super().compute_from(start)

    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> bool:
        current = flight_points[-1]
        if self.target.CL == "optimal":
            # Optimal altitude is based on a target Mach number, though target speed
            # may be specified as TAS or EAS. If so, Mach number has to be computed
            # for target altitude and speed.

            # First, as target speed is expected to be set to "constant" for one
            # parameter. Let's get the real value from start point.
            target_speed = FlightPoint(self.target)
            for speed_param in ["true_airspeed", "equivalent_airspeed", "mach"]:
                if isinstance(target_speed.get(speed_param), str):
                    target_speed[speed_param] = flight_points[0][speed_param]

            # Now, let's compute target Mach number
            atm = AtmosphereSI(max(self.target.altitude, current.altitude))
            if target_speed.equivalent_airspeed:
                target_speed.true_airspeed = atm.get_true_airspeed(target_speed.equivalent_airspeed)
            if target_speed.true_airspeed:
                target_speed.mach = target_speed.true_airspeed / atm.speed_of_sound

            # Mach number has to be capped by self.maximum_mach
            target_mach = min(target_speed.mach, self.maximum_mach)

            # Now we compute target altitude
            self.target.altitude = self._get_optimal_altitude(
                current.mass, target_mach, current.altitude
            )

        if self.target.altitude:
            return self.target.altitude - current.altitude
        elif self.target.true_airspeed:
            return self.target.true_airspeed - current.true_airspeed
        elif self.target.equivalent_airspeed:
            return self.target.equivalent_airspeed - current.equivalent_airspeed
        elif self.target.mach:
            return self.target.mach - current.mach

    def _get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        gamma = (thrust - drag) / mass / g
        return gamma, 0.0
