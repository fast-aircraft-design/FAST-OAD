"""Structure for managing flight point data."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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

from dataclasses import dataclass
from typing import Mapping

from fastoad.constants import EngineSetting


@dataclass
class FlightPoint:
    """
    Dataclass for storing data for one flight point.

    .. note::

        A pandas DataFrame can be generated from a list of FlightPoint instances.
    """

    time: float = 0.0  #: Time in seconds.
    altitude: float = None  #: Altitude in meters.
    ground_distance: float = 0.0  #: Covered ground distance in meters.
    mass: float = None  #: Mass in kg.
    true_airspeed: float = None  #: True airspeed (TAS) in m/s.
    equivalent_airspeed: float = None  #: Equivalent airspeed (EAS) in m/s.
    mach: float = None  #: Mach number.
    engine_setting: EngineSetting = None  #: Engine setting.
    #: Lift coefficient.
    CL: float = None  # pylint: disable=invalid-name
    #: Drag coefficient.
    CD: float = None  # pylint: disable=invalid-name
    drag: float = None  #: Aircraft drag in Newtons.
    thrust: float = None  #: Thrust in Newtons.
    thrust_rate: float = None  #: Thrust rate (between 0. and 1.)

    #: If True, propulsion should match the thrust value.
    #: If False, propulsion should match thrust rate.
    thrust_is_regulated: bool = None

    sfc: float = None  #: Specific Fuel Consumption in kg/N/s.
    slope_angle: float = None  #: Slope angle in radians.
    acceleration: float = None  #: Acceleration value in m/s**2.
    name: str = None  #: Name of current phase.

    @classmethod
    def create_from(cls, data: Mapping) -> "FlightPoint":
        """
        Instantiate FlightPoint from provided data

        :param data: a dict-like instance where keys are FlightPoint attribute names
        :return: the created FlightPoint instance
        """
        return cls(**dict(data))
