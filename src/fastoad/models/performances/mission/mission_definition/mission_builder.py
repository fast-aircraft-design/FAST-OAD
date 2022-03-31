"""
Mission generator.
"""
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

from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from numbers import Number
from typing import Dict, Iterable, List, Mapping, Optional, Union

import numpy as np
import openmdao.api as om
import pandas as pd

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import IPropulsion
from fastoad.openmdao.variables import Variable, VariableList
from .exceptions import FastMissionFileMissingMissionNameError
from .schema import (
    CLIMB_PARTS_TAG,
    CRUISE_PART_TAG,
    DESCENT_PARTS_TAG,
    MISSION_DEFINITION_TAG,
    MissionDefinition,
    PARTS_TAG,
    PHASE_DEFINITIONS_TAG,
    PHASE_TAG,
    RESERVE_TAG,
    ROUTE_DEFINITIONS_TAG,
    SEGMENT_TAG,
)
from ..base import FlightSequence, IFlightPart
from ..polar import Polar
from ..routes import RangedRoute
from ..segments.base import FlightSegment, SegmentDefinitions

# FIXME: should be set in Route class
BASE_UNITS = {
    "range": "m",
    "distance_accuracy": "m",
}


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
    prefix: str = ""

    #: Unit used for self.value. Automatically determined from self.parameter_name,
    #: mainly from unit definition for FlightPoint class.
    output_unit: Optional[str] = field(default=None, init=False, repr=False)

    #: True if the opposite value should be used, if input is defined by a variable.
    _use_opposite: bool = field(default=False, init=False, repr=True)

    _variable_name: Optional[str] = field(default=None, init=False, repr=True)

    def __post_init__(self):

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

        # This is done at end of initialization, because self.variable_name property may need
        # data as self.parameter_name, self.prefix...
        if isinstance(self.input_value, str) and (
            ":" in self.input_value or self.input_value.startswith(("~", "-~"))
        ):
            self.variable_name = self.input_value
            self.input_value = None

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
    def from_dict(cls, parameter_name, definition_dict: dict, prefix=None):
        """
        Instantiates InputDefinition from definition_dict.

        definition_dict["value"] is used as `input_value` in instantiation. It can be an actual
        value or a variable name.

        :param parameter_name: used if definition_dict["value"] == "~" (or "-~")
        :param definition_dict: dict with keys ("value", "unit", "default"). "unit" and "default"
                                are optional.
        :param prefix: used if "~" is in definition_dict["value"]
        """
        if "value" not in definition_dict:
            return None

        input_def = cls(
            parameter_name,
            definition_dict["value"],
            input_unit=definition_dict.get("unit"),
            default_value=definition_dict.get("default", np.nan),
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
            shape_by_conn = self.variable_name.endswith(":CD") or self.variable_name.endswith(":CL")
            return Variable(
                name=self.variable_name,
                val=self.default_value,
                shape_by_conn=shape_by_conn,
                units=self.input_unit,
                desc="Input defined by the mission.",
            )
        return None

    @property
    def variable_name(self):
        """Associated variable name."""
        return self._variable_name

    @variable_name.setter
    def variable_name(self, var_name: Optional[str]):
        if isinstance(var_name, str):
            self._use_opposite = var_name.startswith("-")
            var_name = var_name.strip("- ")

            if var_name.startswith("~"):
                # If value is "~", the parameter name in the mission file is used as suffix.
                # Otherwise, the string after the "~" is used as suffix.
                suffix = var_name.strip("~")
                replacement = self.prefix + ":"
                if suffix == "":
                    replacement += self.parameter_name

                var_name = var_name.replace("~", replacement)

            self._variable_name = var_name
        else:
            self._variable_name = None

    def __str__(self):
        return str(self.value)


class MissionBuilder:
    def __init__(
        self,
        mission_definition: Union[str, MissionDefinition],
        *,
        propulsion: IPropulsion = None,
        reference_area: float = None,
    ):
        """
        This class builds and computes a mission from a provided definition.

        :param mission_definition: a file path or MissionDefinition instance
        :param propulsion: if not provided, the property :attr:`propulsion` must be
                           set before calling :meth:`build`
        :param reference_area: if not provided, the property :attr:`reference_area` must be
                               set before calling :meth:`build`
        """
        self._input_definitions: Dict[str, List[InputDefinition]] = {}
        self.definition = mission_definition
        self._base_kwargs = {"reference_area": reference_area, "propulsion": propulsion}

    @property
    def definition(self) -> MissionDefinition:
        """
        The mission definition instance.

        If it is set as a file path, then the matching file will be read and interpreted.
        """
        return self._definition

    @definition.setter
    def definition(self, mission_definition: Union[str, MissionDefinition]):
        if isinstance(mission_definition, str):
            self._definition = MissionDefinition(mission_definition)
        else:
            self._definition = mission_definition

        self._structure = self._build_structure()

        for mission_name, mission_structure in self._structure.items():
            self._input_definitions[mission_name] = []
            self._parse_inputs(mission_name, mission_structure)

    @property
    def propulsion(self) -> IPropulsion:
        """Propulsion model for performance computation."""
        return self._base_kwargs["propulsion"]

    @propulsion.setter
    def propulsion(self, propulsion: IPropulsion):
        self._base_kwargs["propulsion"] = propulsion

    @property
    def reference_area(self) -> float:
        """Reference area for aerodynamic polar."""
        return self._base_kwargs["reference_area"]

    @reference_area.setter
    def reference_area(self, reference_area: float):
        self._base_kwargs["reference_area"] = reference_area

    def build(self, inputs: Optional[Mapping] = None, mission_name: str = None) -> FlightSequence:
        """
        Builds the flight sequence from definition file.

        :param inputs: if provided, any input parameter that is a string which matches
                       a key of `inputs` will be replaced by the corresponding value
        :param mission_name: mission name (can be omitted if only one mission is defined)
        :return:
        """
        for mission_input_list in self._input_definitions.values():
            for input_def in mission_input_list:
                input_def.set_variable_value(inputs)
        if mission_name is None:
            mission_name = self.get_unique_mission_name()
        mission = self._build_mission(self._structure[mission_name])
        self._propagate_name(mission, mission.name)
        return mission

    def get_route_ranges(
        self, inputs: Optional[Mapping] = None, mission_name: str = None
    ) -> List[float]:
        """

        :param inputs: if provided, any input parameter that is a string which matches
                       a key of `inputs` will be replaced by the corresponding value
        :param mission_name: mission name (can be omitted if only one mission is defined)
        :return: list of flight ranges for each element of the flight sequence that is a route
        """
        routes = self.build(inputs, mission_name).flight_sequence
        return [route.flight_distance for route in routes if isinstance(route, RangedRoute)]

    def get_reserve(self, flight_points: pd.DataFrame, mission_name: str = None) -> float:
        """
        Computes the reserve fuel according to definition in mission input file.

        :param flight_points: the dataframe returned by compute_from() method of the
                              instance returned by :meth:`build`
        :param mission_name: mission name (can be omitted if only one mission is defined)
        :return: the reserve fuel mass in kg, or 0.0 if no reserve is defined.
        """

        if mission_name is None:
            mission_name = self.get_unique_mission_name()

        last_part_spec = self.definition[MISSION_DEFINITION_TAG][mission_name][PARTS_TAG][-1]
        if RESERVE_TAG in last_part_spec:
            ref_name = last_part_spec[RESERVE_TAG]["ref"].value
            multiplier = last_part_spec[RESERVE_TAG]["multiplier"].value

            route_points = flight_points.loc[
                flight_points.name.str.contains("%s:%s" % (mission_name, ref_name))
            ]
            consumed_mass = route_points.mass.iloc[0] - route_points.mass.iloc[-1]
            return consumed_mass * multiplier

        return 0.0

    def get_input_variables(self, mission_name=None) -> VariableList:
        """
        Identify variables for a defined mission.

        :param mission_name: mission name (can be omitted if only one mission is defined)
        :return: a VariableList instance.
        """
        if mission_name is None:
            mission_name = self.get_unique_mission_name()

        input_definition = VariableList()
        for input_def in self._input_definitions[mission_name]:
            if (
                input_def._variable_name
                and input_def._variable_name not in input_definition.names()
            ):
                input_definition.append(input_def.get_input_definition())

        return input_definition

    def get_unique_mission_name(self) -> str:
        """
        Provides mission name if only one mission is defined in mission file.

        :return: the mission name, if only one mission is defined
        :raise FastMissionFileMissingMissionNameError: if several missions are defined in mission
                                                       file
        """
        if len(self._structure) == 1:
            return list(self._structure.keys())[0]

        raise FastMissionFileMissingMissionNameError(
            "Mission name must be specified if several missions are defined in mission file."
        )

    def _build_structure(self) -> OrderedDict:
        """
        Builds mission structures.

        Unlike definition that is a mirror of the definition file, mission structures are
        a mirror of the matching missions, so that building the actual mission instance will
        just be a translation of the structure.
        E.g., the definition can contain a phase that is defined once, but used in several routes.
        The structure will define each route with the complete definition of the phase in each one.

        The returned dict has mission names as keys and mission structures as values.
        """
        structure = OrderedDict()
        structure.update(deepcopy(self.definition[MISSION_DEFINITION_TAG]))
        for mission_name, mission_definition in self.definition[MISSION_DEFINITION_TAG].items():
            mission_structure = OrderedDict({"mission": mission_name})
            mission_structure.update(self._build_mission_structure(mission_definition))
            structure[mission_name] = mission_structure
        return structure

    def _build_mission_structure(self, mission_definition) -> OrderedDict:
        """Builds structure of a mission from its definition."""
        mission_structure = OrderedDict()
        mission_structure.update(deepcopy(mission_definition))
        mission_parts = []
        for part_definition in mission_definition[PARTS_TAG]:
            if "route" in part_definition:
                route_name = part_definition["route"]
                route_structure = OrderedDict({"route": route_name})
                route_structure.update(
                    self._build_route_structure(self.definition[ROUTE_DEFINITIONS_TAG][route_name])
                )
                mission_parts.append(route_structure)
            elif "phase" in part_definition:
                phase_name = part_definition["phase"]
                phase_definition = OrderedDict({"phase": phase_name})
                phase_definition.update(
                    deepcopy(self.definition[PHASE_DEFINITIONS_TAG][phase_name])
                )
                mission_parts.append(phase_definition)
            else:
                mission_parts.append(part_definition)

        mission_structure[PARTS_TAG] = mission_parts
        return mission_structure

    def _build_route_structure(self, route_definition) -> OrderedDict:
        """Builds structure of a route from its definition."""
        route_structure = OrderedDict()
        route_structure.update(deepcopy(route_definition))

        route_structure[CLIMB_PARTS_TAG] = self._get_route_climb_or_descent_structure(
            route_definition[CLIMB_PARTS_TAG]
        )
        route_structure[DESCENT_PARTS_TAG] = self._get_route_climb_or_descent_structure(
            route_definition[DESCENT_PARTS_TAG]
        )

        return route_structure

    def _get_route_climb_or_descent_structure(self, definition):
        parts = []
        for part_definition in definition:
            phase_name = part_definition["phase"]
            phase_structure = OrderedDict({"phase": phase_name})
            phase_structure.update(deepcopy(self.definition[PHASE_DEFINITIONS_TAG][phase_name]))
            parts.append(phase_structure)
        return parts

    def _build_mission(self, mission_structure: OrderedDict) -> FlightSequence:
        """
        Builds mission instance from provided structure.

        :param mission_structure: structure of the mission to build
        :return: the mission instance
        """
        mission = FlightSequence()

        mission.name = mission_structure["mission"]
        for part_spec in mission_structure[PARTS_TAG]:
            if "route" in part_spec:
                part = self._build_route(part_spec)
            elif "phase" in part_spec:
                part = self._build_phase(part_spec)
            elif "segment" in part_spec:
                part = self._build_segment(part_spec, {})
            else:  # reserve definition is used differently
                continue
            part.name = list(part_spec.values())[0]
            mission.flight_sequence.append(part)

        return mission

    def _build_route(self, route_structure: OrderedDict):
        """
        Builds route instance.

        :param route_structure: structure of the route to build
        :return: the route instance
        """
        climb_phases = []
        descent_phases = []

        for part_structure in route_structure[CLIMB_PARTS_TAG]:
            phase = self._build_phase(part_structure)
            climb_phases.append(phase)
            phase.name = list(part_structure.values())[0]

        cruise_phase = self._build_segment(
            route_structure[CRUISE_PART_TAG],
            {"name": "cruise", "target": FlightPoint(ground_distance=0.0)},
        )
        cruise_phase.name = "cruise"

        for part_structure in route_structure[DESCENT_PARTS_TAG]:
            phase = self._build_phase(part_structure)
            descent_phases.append(phase)
            phase.name = list(part_structure.values())[0]

        if "range" in route_structure:
            flight_range = route_structure["range"].value
            route = RangedRoute(
                climb_phases, cruise_phase, descent_phases, flight_distance=flight_range
            )
        else:
            route = FlightSequence()
            route.flight_sequence.extend(climb_phases)

        if "distance_accuracy" in route_structure:
            route.distance_accuracy = route_structure["distance_accuracy"].value

        return route

    def _build_phase(self, phase_structure):
        """
        Builds phase instance

        :param phase_structure: structure of the phase to build
        :return: the phase instance
        """
        phase = FlightSequence()
        kwargs = {name: value for name, value in phase_structure.items() if name != PARTS_TAG}
        self._replace_input_definitions_by_values(kwargs)
        del kwargs[PHASE_TAG]

        for part_structure in phase_structure[PARTS_TAG]:
            segment = self._build_segment(part_structure, kwargs)
            phase.flight_sequence.append(segment)

        return phase

    def _build_segment(
        self, segment_definition: dict, kwargs: dict, tag=SEGMENT_TAG
    ) -> FlightSegment:
        """
        Builds a flight segment according to provided definition.

        :param segment_definition: the segment definition from mission file
        :param kwargs: a preset of keyword arguments for FlightSegment instantiation
        :param tag: the expected tag for specifying the segment type
        :return: the FlightSegment instance
        """
        segment_class = SegmentDefinitions.get_segment_class(str(segment_definition[tag]))
        part_kwargs = kwargs.copy()
        part_kwargs.update(
            {name: value for name, value in segment_definition.items() if name != tag}
        )
        part_kwargs.update(self._base_kwargs)
        for key, value in part_kwargs.items():
            if key == "polar":
                value = Polar(value["CL"].value, value["CD"].value)
            elif key == "target":
                if not isinstance(value, FlightPoint):
                    target_parameters = {
                        param.parameter_name: param.value for param in value.values()
                    }
                    relative_fields = [
                        param.parameter_name for param in value.values() if param.is_relative
                    ]
                    value = FlightPoint(**target_parameters)
                    value.set_as_relative(relative_fields)

            part_kwargs[key] = value

        self._replace_input_definitions_by_values(part_kwargs)

        if "engine_setting" in part_kwargs:
            part_kwargs["engine_setting"] = EngineSetting.convert(part_kwargs["engine_setting"])

        segment = segment_class(**part_kwargs)
        return segment

    @staticmethod
    def _replace_input_definitions_by_values(part_kwargs):
        for key, input_def in part_kwargs.items():
            if isinstance(input_def, InputDefinition):
                part_kwargs[key] = input_def.value

    def _propagate_name(self, part: IFlightPart, new_name: str):
        """
        Changes the `name` property of all flight sub-parts of provided IFlightPart instance.

        If a subpart has a non-empty name, its new name is its old name, prepended with `new_name`.
        Otherwise, its names becomes the one of its parent after modification.

        :param part:
        :param new_name:
        """
        part.name = new_name
        if isinstance(part, FlightSequence):
            for subpart in part.flight_sequence:
                if subpart.name:
                    self._propagate_name(subpart, ":".join([str(part.name), str(subpart.name)]))
                else:
                    subpart.name = part.name

    def _parse_inputs(self, mission_name, definition, parent=None, prefix=None):
        if prefix is None:
            prefix = "data:mission"

        if isinstance(definition, dict):
            for key, value in definition.items():
                name = (
                    str(definition.get("mission", ""))
                    + str(definition.get("route", ""))
                    + str(definition.get("phase", ""))
                )
                prefix_addition = ":" + name if name else ""

                if isinstance(value, list):
                    try:
                        _ = np.asarray(value) + 1
                        is_numeric_list = True
                    except TypeError:
                        is_numeric_list = False

                if isinstance(value, dict) and "value" in value.keys():
                    if value["value"] is None:
                        value["value"] = "~"
                    definition[key] = InputDefinition.from_dict(
                        key, definition[key], prefix=prefix + prefix_addition
                    )
                    self._input_definitions[mission_name].append(definition[key])
                elif not isinstance(value, dict) and (
                    not isinstance(value, list) or is_numeric_list
                ):
                    if value is None:
                        # "~" alone is interpreted as "null" by the yaml parser
                        # We get back to "~" to make the next step easier.
                        value = "~"
                    definition[key] = InputDefinition(key, value, prefix=prefix + prefix_addition)
                    self._input_definitions[mission_name].append(definition[key])
                else:
                    self._parse_inputs(
                        mission_name, value, parent=key, prefix=prefix + prefix_addition
                    )
        elif isinstance(definition, list):
            for value in definition:
                self._parse_inputs(mission_name, value, parent=parent, prefix=prefix)
