"""Structure for managing flight point data."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from dataclasses import asdict, dataclass
from typing import Any, List, Mapping

import numpy as np
import pandas as pd

from fastoad.constants import EngineSetting


@dataclass
class FlightPoint:
    """
    Dataclass for storing data for one flight point.

    This class is meant for:

    - pandas friendliness: data exchange with pandas DataFrames is simple
    - extensibility: any user might add fields to the **class** using :meth:`add_field`

    **Exchanges with pandas DataFrame**

        A pandas DataFrame can be generated from a list of FlightPoint instances::

            >>> import pandas as pd
            >>> from fastoad.model_base import FlightPoint

            >>> fp1 = FlightPoint(mass=70000., altitude=0.)
            >>> fp2 = FlightPoint(mass=60000., altitude=10000.)
            >>> df = pd.DataFrame([fp1, fp2])

        And FlightPoint instances can be created from DataFrame rows::

            # Get one FlightPoint instance from a DataFrame row
            >>> fp1bis = FlightPoint.create(df.iloc[0])

            # Get a list of FlightPoint instances from the whole DataFrame
            >>> flight_points = FlightPoint.create_list(df)

    **Extensibility**

        FlightPoint class is bundled with several fields that are commonly used in trajectory
        assessment, but one might need additional fields.

        Python allows to add attributes to any instance at runtime, but for FlightPoint to run
        smoothly, especially when exchanging data with pandas, you have to work at class level.
        This can be done using :meth:`add_field`, preferably outside of any class or function::

            # Adds a float field with None as default value
            >>> FlightPoint.add_field("ion_drive_power")

            # Adds a field and define its type and default value
            >>> FlightPoint.add_field("warp", annotation_type=int, default_value=9)

            # Now these fields can be used at instantiation
            >>> fp = FlightPoint(ion_drive_power=110.0, warp=12)

            # Removes a field, even an original one (useful only to avoid having it in outputs)
            >>> FlightPoint.remove_field("sfc")

    .. note::

        All parameters in FlightPoint instances are expected to be in SI units.

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

    _units = dict(
        time="s",
        altitude="m",
        ground_distance="m",
        mass="kg",
        true_airspeed="m/s",
        equivalent_airspeed="m/s",
        mach="-",
        CL="-",
        CD="-",
        drag="N",
        thrust="N",
        thrust_rate="-",
        sfc="kg/N/s",
        slope_angle="rad",
        acceleration="m/s**2",
    )

    @classmethod
    def get_units(cls) -> dict:
        """
        Returns (field name, unit) dict for any field that has a defined unit.

        A dimensionless physical quantity will have "-" as unit.
        """
        return cls._units

    @classmethod
    def create(cls, data: Mapping) -> "FlightPoint":
        """
        Instantiate FlightPoint from provided data.

        `data` can typically be a dict or a pandas DataFrame row.

        :param data: a dict-like instance where keys are FlightPoint attribute names
        :return: the created FlightPoint instance
        """
        return cls(**dict(data))

    @classmethod
    def create_list(cls, data: pd.DataFrame) -> List["FlightPoint"]:
        """
        Creates a list of FlightPoint instances from provided DataFrame.

        :param data: a dict-like instance where keys are FlightPoint attribute names
        :return: the created FlightPoint instance
        """
        return [cls.create(row) for row in data.iloc]

    @classmethod
    def add_field(cls, name: str, annotation_type=float, default_value: Any = None, unit=None):
        """
        Adds the named field to FlightPoint class.

        If the field name already exists, the field is redefined.

        :param name: field name
        :param annotation_type: field type
        :param default_value: field default value
        :param unit: expected unit for the added field ("-" should be provided for a dimensionless
                     physical quantity)
        """
        cls.remove_field(name)

        del cls.__init__  # Delete constructor to allow it being rebuilt with dataclass() call
        setattr(cls, name, default_value)
        cls.__annotations__[name] = annotation_type
        dataclass(cls)
        if unit:
            cls._units[name] = unit

    @classmethod
    def remove_field(cls, name):
        """
        Removes the named field from FlightPoint class.

        :param name: field name
        """
        if name in cls.__annotations__:
            del cls.__init__  # Delete constructor to allow it being rebuilt with dataclass() call
            delattr(cls, name)
            del cls.__annotations__[name]
            dataclass(cls)
            if name in cls._units:
                del cls._units[name]

    def scalarize(self):
        """
        Convenience method for converting to scalars all fields that have a
        one-item array-like value.
        """
        self_as_dict = asdict(self)
        for field_name, value in self_as_dict.items():
            if np.size(value) == 1:
                setattr(self, field_name, np.asarray(value).item())
