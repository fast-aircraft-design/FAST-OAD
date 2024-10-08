"""Structure for managing flight point data."""

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

from copy import deepcopy
from dataclasses import asdict, dataclass, field, fields
from numbers import Number
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

import pandas as pd

from fastoad._utils.arrays import scalarize
from fastoad.constants import EngineSetting

FIELD_DESCRIPTOR = "field_descriptor"


@dataclass
class _FieldDescriptor:
    """
    Class to be used as dataclass field metadata.
    """

    is_cumulative: Optional[bool] = False
    unit: Optional[str] = None


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
        This can be done using :meth:`add_field`, preferably outside any class or function::

            # Adding a float field with None as default value
            >>> FlightPoint.add_field(
            ...    "ion_drive_power",
            ...    unit="W",
            ...    is_cumulative=False, # Tells if quantity sums up during mission
            ...    )

            # Adding a field and defining its type and default value
            >>> FlightPoint.add_field("warp", annotation_type=int, default_value=9)

            # Now these fields can be used at instantiation
            >>> fp = FlightPoint(ion_drive_power=110.0, warp=12)

            # Removing a field, even an original one
            >>> FlightPoint.remove_field("sfc")

    .. note::

        All original parameters in FlightPoint instances are expected to be in SI units.

    """

    #: Time in seconds.
    time: float = field(
        default=0.0, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(is_cumulative=True, unit="s")}
    )

    #: Altitude in meters.
    altitude: float = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="m")})

    #: temperature deviation from Standard Atmosphere
    isa_offset: float = field(default=0.0, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="K")})

    #: Covered ground distance in meters.
    ground_distance: float = field(
        default=0.0, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(is_cumulative=True, unit="m")}
    )

    #: Mass in kg.
    mass: float = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="kg")})

    #: Consumed fuel since mission start, in kg.
    consumed_fuel: float = field(
        default=0.0, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(is_cumulative=True, unit="kg")}
    )

    #: True airspeed (TAS) in m/s.
    true_airspeed: float = field(
        default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="m/s")}
    )

    #: Equivalent airspeed (EAS) in m/s.
    equivalent_airspeed: float = field(
        default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="m/s")}
    )

    #: Mach number.
    mach: float = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="-")})

    #: Engine setting.
    engine_setting: EngineSetting = field(
        default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor()}
    )

    # pylint: disable=invalid-name
    #: Lift coefficient.
    CL: float = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="-")})

    # pylint: disable=invalid-name
    #: Drag coefficient.
    CD: float = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="-")})

    #: Aircraft lift in Newtons
    lift: float = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="N")})

    #: Aircraft drag in Newtons.
    drag: float = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="N")})

    #: Thrust in Newtons.
    thrust: float = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="N")})

    #: Thrust rate (between 0. and 1.)
    thrust_rate: float = field(
        default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="-")}
    )

    #: If True, propulsion should match the thrust value.
    #: If False, propulsion should match thrust rate.
    thrust_is_regulated: bool = field(
        default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="-")}
    )

    #: Specific Fuel Consumption in kg/N/s.
    sfc: float = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="kg/N/s")})

    #: Slope angle in radians.
    slope_angle: float = field(
        default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="rad")}
    )

    #: Acceleration value in m/s**2.
    acceleration: float = field(
        default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="m/s**2")}
    )

    #: angle of attack in radians
    alpha: float = field(default=0.0, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="rad")})

    #: slope angle derivative in rad/s
    slope_angle_derivative: float = field(
        default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor(unit="rad/s")}
    )

    #: Name of current phase.
    name: str = field(default=None, metadata={FIELD_DESCRIPTOR: _FieldDescriptor()})

    # Will store field metadata when needed. Must be accessed through _get_field_descriptors()
    __field_descriptors = {}

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
        for cls_field in fields(new_point):
            reference_value = getattr(reference_point, cls_field.name)
            target_value = getattr(new_point, cls_field.name)
            if isinstance(target_value, Number) and new_point.is_relative(cls_field.name):
                setattr(new_point, cls_field.name, reference_value + target_value)
                new_point.set_as_absolute(cls_field.name)
        new_point.scalarize()
        return new_point

    def scalarize(self):
        """
        Convenience method for converting to scalars all fields that have a
        one-item array-like value.
        """
        self_as_dict = asdict(self)
        for field_name, value in self_as_dict.items():
            setattr(self, field_name, scalarize(value))

    @classmethod
    def get_field_names(cls):
        """
        :return: names of all fields of the flight point.
        """
        return [cls_field.name for cls_field in fields(cls) if not cls_field.name.startswith("_")]

    @classmethod
    def get_units(cls) -> dict:
        """
        Returns (field name, unit) dict for any field that has a defined unit.

        A dimensionless physical quantity will have "-" as unit.
        """
        return {
            name: field_descriptor.unit
            for name, field_descriptor in cls._get_field_descriptors().items()
        }

    @classmethod
    def get_unit(cls, field_name) -> Optional[str]:
        """
        Returns unit for asked field.

        A dimensionless physical quantity will have "-" as unit.
        """
        return cls._get_field_descriptor(field_name).unit

    @classmethod
    def is_cumulative(cls, field_name) -> Optional[bool]:
        """
        Tells if asked field is cumulative (sums up during mission).

        Returns None if field not found.
        """
        return cls._get_field_descriptor(field_name).is_cumulative

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
    def add_field(
        cls,
        name: str,
        annotation_type=float,
        default_value: Any = None,
        unit="-",
        is_cumulative=False,
    ):
        """
        Adds the named field to FlightPoint class.

        If the field name already exists, the field is redefined.

        :param name: field name
        :param annotation_type: field type
        :param default_value: field default value
        :param unit: expected unit for the added field. "-" should be provided for a dimensionless
                     physical quantity. Set to None, when unit concept does not apply.
        :param is_cumulative: True if field value is summed up during mission
        """
        cls._redeclare_fields()

        del cls.__init__  # Delete constructor to allow it being rebuilt with dataclass() call
        setattr(
            cls,
            name,
            field(
                default=default_value,
                metadata={
                    FIELD_DESCRIPTOR: _FieldDescriptor(unit=unit, is_cumulative=is_cumulative)
                },
            ),
        )
        cls.__annotations__[name] = annotation_type
        dataclass(cls)

    @classmethod
    def remove_field(cls, name):
        """
        Removes the named field from FlightPoint class.

        :param name: field name
        """
        if name in cls.__annotations__:
            cls._redeclare_fields()
            del cls.__init__  # Delete constructor to allow it being rebuilt with dataclass() call
            delattr(cls, name)
            del cls.__annotations__[name]
            dataclass(cls)

    @classmethod
    def _get_field_descriptors(cls) -> Dict[str, _FieldDescriptor]:
        """
        Uses this method instead of accessing cls.__field_descriptors to ensure it
        will always be correctly populated.
        """
        if not cls.__field_descriptors:
            cls.__field_descriptors = {
                cls_field.name: cls_field.metadata[FIELD_DESCRIPTOR]
                for cls_field in fields(cls)
                if not cls_field.name.startswith("_")
            }

        return cls.__field_descriptors

    @classmethod
    def _get_field_descriptor(cls, field_name) -> _FieldDescriptor:
        """
        Returns the _FieldDescriptor class for provided field_name.
        Returns _FieldDescriptor(None, None, None) if field_name is not present.
        """
        return cls._get_field_descriptors().get(field_name, _FieldDescriptor(None, None))

    @classmethod
    def _redeclare_fields(cls):
        """
        To be done before "re-dataclassing" cls.

        In current state, fields are now declared using only default value (no metadata). We have
        to redo the field declaration properly.
        """
        for cls_field in fields(cls):
            setattr(
                cls, cls_field.name, field(default=cls_field.default, metadata=cls_field.metadata)
            )

        cls.__field_descriptors = {}  # Will need to rebuild this dict on next usage.
