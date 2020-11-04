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


# Set of dictionary keys that are mapped to instance attributes.
from typing import Mapping

LABELS = {
    "time": dict(default=0.0, doc="Time in seconds."),
    "altitude": dict(doc="Altitude in meters."),
    "ground_distance": dict(default=0.0, doc="Covered ground distance in meters."),
    "mass": dict(doc="Mass in kg."),  # in kg
    "true_airspeed": dict(doc="True airspeed (TAS) in m/s."),
    "equivalent_airspeed": dict(doc="Equivalent airspeed (EAS) in m/s."),
    "mach": dict(doc="Mach number."),
    "engine_setting": dict(doc="Engine setting (see :class:`~fastoad.constants.EngineSetting`)."),
    "CL": dict(doc="Lift coefficient."),
    "CD": dict(doc="Drag coefficient."),
    "drag": dict(doc="Aircraft drag in Newtons."),
    "thrust": dict(doc="Thrust in Newtons."),
    "thrust_rate": dict(doc="Thrust rate (between 0. and 1.)"),
    "thrust_is_regulated": dict(
        doc="Boolean. If True, propulsion should match the thrust value. "
        "If False, propulsion should match thrust rate."
    ),
    "sfc": dict(doc="Specific Fuel Consumption in kg/N/s."),
    "slope_angle": dict(doc="Slope angle in radians."),
    "acceleration": dict(doc="Acceleration value in m/s**2."),
    "name": dict(default="", doc="Name of current phase."),
}


# @AddKeyAttributes(LABELS)
@dataclass
class FlightPoint:
    """
    Class for storing data for one flight point.

    An instance is a simple dict, but for convenience, each item can be accessed
    as an attribute (inspired by pandas DataFrames). Hence, one can write::

        >>> fp = FlightPoint(speed=250., altitude=10000.)
        >>> fp["speed"]
        250.0
        >>> fp2 = FlightPoint({"speed":150., "altitude":5000.})
        >>> fp2.speed
        250.0
        >>> fp["mass"] = 70000.
        >>> fp.mass
        70000.0
        >>> fp.mass = 50000.
        >>> fp["mass"]
        50000.0

    .. Note::

        Constructor will forbid usage of unknown keys as keyword argument, but
        other methods will allow them, while not making the matching between dict
        keys and attributes, hence::

            >>> fp["foo"] = 42  # Ok
            >>> bar = fp.foo  # raises exception !!!!
            >>> fp.foo = 50  # allowed by Python
            >>> # But inner dict is not affected:
            >>> fp.foo
            50
            >>> fp["foo"]
            42

    This class is especially useful for generating pandas DataFrame: a pandas
    DataFrame can be generated from a list of dict... or a list of FlightPoint
    instances.

    The set of dictionary keys that are mapped to instance attributes is given by
    :meth:`get_attribute_keys`.
    """

    time: float = 0.0  # Time in seconds.
    altitude: float = None
    ground_distance: float = 0.0
    mass: float = None
    true_airspeed: float = None
    equivalent_airspeed: float = None
    mach: float = None
    engine_setting: float = None
    CL: float = None
    CD: float = None
    drag: float = None
    thrust: float = None
    thrust_rate: float = None
    thrust_is_regulated: bool = None
    sfc: float = None
    slope_angle: float = None
    acceleration: float = None
    name: str = None

    @classmethod
    def create_from(cls, dict_like: Mapping) -> "FlightPoint":
        return cls(**dict(dict_like))
