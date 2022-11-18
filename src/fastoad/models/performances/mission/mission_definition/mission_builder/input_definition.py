"""Management of mission input definitions."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

from dataclasses import InitVar, dataclass, field
from numbers import Number
from typing import Iterable, Mapping, Optional, Tuple, Union

import numpy as np
from openmdao import api as om

from fastoad.model_base import FlightPoint
from fastoad.openmdao.variables import Variable
from .constants import BASE_UNITS


@dataclass
class InputDefinition:
    """
    Class for managing definition of mission inputs.

    It stores and processes input definition from mission files:
        - provides values to be used for mission computation (management of units and variables)
        - provides information for OpenMDAO declaration
    """

    #: The parameter this input is defined for.
    parameter_name: str

    #: Value, matching `input_unit`. At instantiation, it can also be the variable name.
    input_value: Optional[Union[Number, Iterable, str]]

    #: Unit used for self.input_value.
    input_unit: Optional[str] = None

    #: Default value. Used if value is a variable name.
    default_value: Number = np.nan

    #: True if variable is defined as relative.
    is_relative: bool = False

    #: Prefix used when generating variable name because "~" was used in variable name input.
    part_identifier: str = ""

    #: Unit used for self.value. Automatically determined from self.parameter_name,
    #: mainly from unit definition for FlightPoint class.
    output_unit: Optional[str] = field(default=None, init=False, repr=False)

    #: Value of the "shape" openMDAO flag for input declaration.
    shape: Optional[Tuple[int]] = None

    #: Value of the "shape_by_conn" openMDAO flag for input declaration.
    shape_by_conn: bool = False

    #: Prefix used when replacement of "~" is needed.
    prefix: str = ""

    #: Used only for tests
    variable_name: InitVar[Optional[str]] = None

    #: Used only for tests
    use_opposite: InitVar[Optional[bool]] = None

    #: True if the opposite value should be used, if input is defined by a variable.
    _use_opposite: bool = field(default=False, init=False, repr=True)

    _variable_name: Optional[str] = field(default=None, init=False, repr=True)

    def __post_init__(self, variable_name, use_opposite):

        if self.parameter_name.startswith("delta_"):
            self.is_relative = True
            self.parameter_name = self.parameter_name[6:]

        self.output_unit = FlightPoint.get_units().get(self.parameter_name)
        if self.output_unit is None:
            self.output_unit = BASE_UNITS.get(self.parameter_name)
        if self.output_unit == "-":
            self.output_unit = None

        if self.input_unit is None:
            self.input_unit = self.output_unit

        if variable_name and not isinstance(variable_name, property):
            # dataclass "feature": default value of 'variable_name' is 'property' because it
            # is defined as a property.
            self.variable_name = variable_name
            self.input_value = None
        elif isinstance(self.input_value, str) and (
            ":" in self.input_value or self.input_value.startswith(("~", "-~"))
        ):
            # This is done at end of initialization, because self.variable_name property may need
            # data as self.parameter_name, self.prefix...
            self.variable_name = self.input_value
            self.input_value = None

        if use_opposite is not None:
            self._use_opposite = use_opposite

    @property
    def value(self):
        """

        :return: Value of variable in DEFAULT unit (unit used by mission calculation),
                 or None if input is a variable and set_variable_input() has NOT been called,
                 or the unchanged value if it is not a number.
        """
        try:
            return om.convert_units(self.input_value, self.input_unit, self.output_unit)
        except TypeError:
            return self.input_value

    @classmethod
    def from_dict(cls, parameter_name, definition_dict: dict, part_identifier=None, prefix=None):
        """
        Instantiates InputDefinition from definition_dict.

        definition_dict["value"] is used as `input_value` in instantiation. It can be an actual
        value or a variable name.

        :param parameter_name: used if definition_dict["value"] == "~" (or "-~")
        :param definition_dict: dict with keys ("value", "unit", "default"). "unit" and "default"
                                are optional.
        :param part_identifier: used if "~" is in definition_dict["value"]
        :param prefix: used if "~" is in definition_dict["value"]
        """
        if "value" not in definition_dict:
            return None

        input_def = cls(
            parameter_name,
            definition_dict["value"],
            input_unit=definition_dict.get("unit"),
            default_value=definition_dict.get("default", np.nan),
            shape_by_conn=definition_dict.get("shape_by_conn", False),
            part_identifier=part_identifier,
            prefix=prefix,
        )
        return input_def

    def set_variable_value(self, inputs: Mapping):
        """
        Sets numerical value from OpenMDAO inputs.

        OpenMDAO value is assumed to be provided with unit self.input_unit.

        :param inputs:
        """
        if self.variable_name:
            # Note: OpenMDAO `inputs` object has no `get()` method, so we need to do this:
            value = (
                inputs[self.variable_name] if self.variable_name in inputs else self.default_value
            )
            if self._use_opposite:
                self.input_value = -value
            else:
                self.input_value = value

    def get_input_definition(self) -> Optional[Variable]:
        """
        Provides information for input definition in OpenMDAO.

        :return: Variable instance with input definition, or None if no variable name was defined.
        """
        if self.variable_name:
            return Variable(
                name=self.variable_name,
                val=self.default_value,
                shape_by_conn=self.shape_by_conn,
                units=self.input_unit,
                desc="Input defined by the mission.",
            )
        return None

    # pylint: disable=function-redefined  # the variable_name field is an InitVar.
    @property
    def variable_name(self):
        """Associated variable name."""
        return self._variable_name

    @variable_name.setter
    def variable_name(self, var_name: Optional[str]):
        if isinstance(var_name, str):
            self._use_opposite = var_name.startswith("-")
            var_name = var_name.strip("- ")

            if "~" in var_name:
                # We authorize colons next to "~", but we do as they were not present.
                var_name = var_name.replace(":~", "~").replace("~:", "~")
                parts = var_name.replace(":~", "~").split("~")
                if len(parts) > 2:
                    # Hidden feature for now: using a double tilda (~~) will trigger
                    # a replacement by the mission name only
                    # (useful for backward compatibility since we need to provide
                    #  "data:mission:<mission_name>:TOW" as variable
                    prefix = parts[0]
                    suffix = parts[-1]
                    part_identifier = self.part_identifier.split(":")[0]
                else:
                    # Standard case with simple tilda
                    prefix, suffix = var_name.replace(":~", "~").split("~")
                    part_identifier = self.part_identifier

                if not prefix:
                    # If nothing before "~", a default value is used
                    prefix = self.prefix
                if not suffix:
                    # If nothing after "~", the parameter name is used
                    suffix = self.parameter_name

                var_name = ":".join([prefix, part_identifier, suffix])

            self._variable_name = var_name
        else:
            self._variable_name = None

    def __str__(self):
        return str(self.value)
