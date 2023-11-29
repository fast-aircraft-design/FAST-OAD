"""Structure for managing flight point data."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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
from copy import deepcopy
from dataclasses import asdict, dataclass, fields
from numbers import Number
from typing import Any, List, Mapping, Sequence, Union

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
    isa_offset: float = 0.0  #: temperature deviation from Standard Atmosphere
    ground_distance: float = 0.0  #: Covered ground distance in meters.
    mass: float = None  #: Mass in kg.
    consumed_fuel: float = 0.0  #: Consumed fuel since mission start, in kg.
    true_airspeed: float = None  #: True airspeed (TAS) in m/s.
    equivalent_airspeed: float = None  #: Equivalent airspeed (EAS) in m/s.
    mach: float = None  #: Mach number.
    engine_setting: EngineSetting = None  #: Engine setting.
    #: Lift coefficient.
    CL: float = None  # pylint: disable=invalid-name
    #: Drag coefficient.
    CD: float = None  # pylint: disable=invalid-name
    lift: float = None  #: Aircraft lift in Newtons
    drag: float = None  #: Aircraft drag in Newtons.
    thrust: float = None  #: Thrust in Newtons.
    thrust_rate: float = None  #: Thrust rate (between 0. and 1.)

    #: If True, propulsion should match the thrust value.
    #: If False, propulsion should match thrust rate.
    thrust_is_regulated: bool = None

    sfc: float = None  #: Specific Fuel Consumption in kg/N/s.
    slope_angle: float = None  #: Slope angle in radians.
    acceleration: float = None  #: Acceleration value in m/s**2.
    alpha: float = 0.0  #: angle of attack in radians
    slope_angle_derivative: float = None  #: slope angle derivative in rad/s
    name: str = None  #: Name of current phase.

    _units = dict(
        time="s",
        altitude="m",
        ground_distance="m",
        mass="kg",
        consumed_fuel="kg",
        true_airspeed="m/s",
        equivalent_airspeed="m/s",
        mach="-",
        CL="-",
        CD="-",
        lift="N",
        drag="N",
        thrust="N",
        thrust_rate="-",
        sfc="kg/N/s",
        slope_angle="rad",
        acceleration="m/s**2",
        alpha="rad",
        slope_angle_derivative="rad/s",
    )

    def __post_init__(self):
        self._relative_parameters = {"ground_distance", "time"}

    def set_as_relative(self, field_names: Union[Sequence[str], str]):
        """
        Makes that values for given field_names will be considered as relative when
        calling :meth:`make_absolute`.

        :param field_names:
        """
        if isinstance(field_names, str):
            self._relative_parameters.add(field_names)
        else:
            self._relative_parameters |= set(field_names)

    def set_as_absolute(self, field_names: Union[Sequence[str], str]):
        """
        Makes that values for given field_names will be considered as absolute when
        calling :meth:`make_absolute`.

        :param field_names:
        """
        if isinstance(field_names, str):
            self._relative_parameters.remove(field_names)
        else:
            self._relative_parameters -= set(field_names)

    def is_relative(self, field_name) -> bool:
        """
        Tells if given field is considered as relative or absolut

        :param field_name:
        :return: True if it is relative
        """
        return field_name in self._relative_parameters

    def make_absolute(self, reference_point: "FlightPoint") -> "FlightPoint":
        """
        Computes a copy flight point where no field is relative.

        :param reference_point: relative fields will be made absolute using this point.
        :return: the copied flight point with no relative field.
        """
        new_point = deepcopy(self)
        for field in fields(new_point):
            reference_value = getattr(reference_point, field.name)
            target_value = getattr(new_point, field.name)
            if isinstance(target_value, Number) and new_point.is_relative(field.name):
                setattr(new_point, field.name, reference_value + target_value)
                new_point.set_as_absolute(field.name)
        new_point.scalarize()
        return new_point

    @classmethod
    def get_field_names(cls):
        """
        :return: names of all fields of the flight point.
        """
        return [field.name for field in fields(cls) if not field.name.startswith("_")]

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
