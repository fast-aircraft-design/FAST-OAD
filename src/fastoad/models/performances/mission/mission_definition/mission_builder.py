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

from abc import ABC, abstractmethod
from collections import ChainMap, OrderedDict
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from itertools import chain
from numbers import Number
from typing import Dict, Iterable, List, Mapping, Optional, Tuple, Union

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
    ROUTE_TAG,
    SEGMENT_TAG,
)
from ..base import FlightSequence
from ..polar import Polar
from ..routes import RangedRoute
from ..segments.base import FlightSegment, SegmentDefinitions

# FIXME: should be set in Route class

NAME_TAG = "name"
TYPE_TAG = "type"
SEGMENT_TYPE_TAG = "segment_type"
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


@dataclass
class AbstractStructureBuilder(ABC):
    """
    Base class for building structures of mission parts.

    "Structures" are dicts that are derived from the mission definition file so that they can be
    readily translated into the matching implementation.

    Usage:

    Subclasses must implement the build method that will create the specific part of the structure
    dict (name and type fields are automated).

    If the structure has to contain the result of another result, :meth:`insert_builder` should
    be used to ensure a correct processing of the global structure, especially to get a correct
    resolution of :attr:`input_definitions`.
    """

    definition: InitVar[dict]
    name: str
    parent_name: str = None

    _structure: OrderedDict = field(default=None, init=False)

    _input_definitions: List[InputDefinition] = field(default_factory=list, init=False)
    _builders: List[Tuple["AbstractStructureBuilder", dict]] = field(
        default_factory=list, init=False
    )

    #: Defined by subclass
    type = None

    def __init_subclass__(cls, *, structure_type=None):
        cls.type = structure_type

    def __post_init__(self, definition):
        self._structure = self._build(definition)
        self._structure[NAME_TAG] = self.qualified_name
        if self.__class__.type:
            self._structure[TYPE_TAG] = self.__class__.type
        self._parse_inputs(self._structure, self._input_definitions)

    @property
    def structure(self) -> OrderedDict:
        """A dictionary that is ready to be translated to the matching implementation."""
        for builder, place_holder in self._builders:
            place_holder.update(builder.structure)
            self._input_definitions += builder.get_input_definitions()
        self._builders = []  # Builders have been used and can be forgotten.
        return self._structure

    def get_input_definitions(self) -> List[InputDefinition]:
        """List of InputDefinition instances in the structure."""
        return self._input_definitions + list(
            chain(*[builder.get_input_definitions() for builder, _ in self._builders])
        )

    def _insert_builder(self, builder: "AbstractStructureBuilder", place_holder: dict):
        """
        Method to be used when another StructureBuilder object is needed in :meth:`build`.

        Not using this method will prevent a correct processing of :attr:`input_definitions`.

        At location where the builder result should be used, an empty dict should be put, and this
        empty dict should be provided as `place_holder` argument.

        :param builder:
        :param place_holder:
        """
        self._builders.append((builder, place_holder))

    @abstractmethod
    def _build(self, definition: dict) -> OrderedDict:
        """
        This method creates the needed structure dict.

        Keys "name" and "type" are not needed, as they will be written later on in the process.

        .. Important::

            Please use :meth:`_insert_builder` when another StructureBuilder object is needed in
            the currently built structure.

        :param definition: the dict that will be converted.
        :return: the structure dict
        """
        pass

    @property
    def qualified_name(self):
        """Name of the current structure, preceded by the parent names, separated by colons (:)."""
        if not self.parent_name:
            return self.name

        name = self.parent_name
        if self.name:
            name += f":{self.name}"
        return name

    def _parse_inputs(self, structure, input_definitions, parent=None, prefix=None):
        """
        Returns the `definition` structure where all inputs (string/numeric values, numeric lists,
        dicts with a "value key"), have been converted to an InputDefinition instance.

        Created InputDefinition instances are stored in self._input_definitions.

        :param structure:
        :param parent:
        :param prefix:
        :return: amended definition
        """
        if prefix is None:
            prefix = "data:mission"

        if isinstance(structure, dict):
            if "value" in structure.keys():
                input_definition = InputDefinition.from_dict(parent, structure, prefix=prefix)
                input_definitions.append(input_definition)
                return input_definition

            name = structure.get(NAME_TAG, "")
            if name:
                prefix = f"data:mission:{name}"

            for key, value in structure.items():
                if key not in [
                    NAME_TAG,
                    TYPE_TAG,
                    SEGMENT_TYPE_TAG,
                    PARTS_TAG,
                    CLIMB_PARTS_TAG,
                    DESCENT_PARTS_TAG,
                    CRUISE_PART_TAG,
                ]:
                    structure[key] = self._parse_inputs(
                        value, input_definitions, parent=key, prefix=prefix
                    )
            return structure
        else:
            input_definition = InputDefinition(parent, structure, prefix=prefix)
            input_definitions.append(input_definition)
            return input_definition


class DefaultStructureBuilder(AbstractStructureBuilder):
    """
    Builder for structures that do not need to process the given definition.

    :param definition: the definition for the part only
    """

    def _build(self, definition: dict) -> OrderedDict:
        return OrderedDict(deepcopy(definition))


class SegmentStructureBuilder(AbstractStructureBuilder, structure_type=SEGMENT_TAG):
    """
    Structure builder for segment definition.

    :param definition: the definition for the segment only
    """

    def _build(self, definition: dict) -> OrderedDict:
        segment_structure = OrderedDict(deepcopy(definition))
        del segment_structure[SEGMENT_TAG]
        segment_structure[SEGMENT_TYPE_TAG] = definition[SEGMENT_TAG]

        return segment_structure


class PhaseStructureBuilder(AbstractStructureBuilder, structure_type=PHASE_TAG):
    """
    Structure builder for phase definition.

    :param definition: the whole content of definition file
    """

    def _build(self, definition: dict) -> OrderedDict:
        phase_definition = definition[PHASE_DEFINITIONS_TAG][self.name]
        phase_structure = OrderedDict(deepcopy(phase_definition))

        for i, part in enumerate(phase_definition[PARTS_TAG]):
            if PHASE_TAG in part:
                builder = PhaseStructureBuilder(definition, part[PHASE_TAG], self.qualified_name)
            elif SEGMENT_TAG in part:
                builder = SegmentStructureBuilder(part, "", self.qualified_name)
            else:
                raise RuntimeError(f"Unexpected structure in definition of phase {self.name}")

            phase_structure[PARTS_TAG][i] = {}
            self._insert_builder(builder, phase_structure[PARTS_TAG][i])

        return phase_structure


class RouteStructureBuilder(AbstractStructureBuilder, structure_type=ROUTE_TAG):
    """
    Structure builder for route definition.

    :param definition: the whole content of definition file
    """

    def _build(self, definition: dict) -> OrderedDict:
        route_definition = definition[ROUTE_DEFINITIONS_TAG][self.name]
        route_structure = OrderedDict(deepcopy(route_definition))

        route_structure[CLIMB_PARTS_TAG] = self._get_route_climb_or_descent_structure(
            definition, route_definition[CLIMB_PARTS_TAG]
        )

        builder = SegmentStructureBuilder(
            route_definition[CRUISE_PART_TAG], "cruise", self.qualified_name
        )
        route_structure[CRUISE_PART_TAG] = {}
        self._insert_builder(builder, route_structure[CRUISE_PART_TAG])

        route_structure[DESCENT_PARTS_TAG] = self._get_route_climb_or_descent_structure(
            definition, route_definition[DESCENT_PARTS_TAG]
        )

        return route_structure

    def _get_route_climb_or_descent_structure(self, global_definition, parts_definition):
        parts = []
        for part_definition in parts_definition:
            phase_name = part_definition["phase"]
            builder = PhaseStructureBuilder(global_definition, phase_name, self.qualified_name)
            phase_structure = {}
            self._insert_builder(builder, phase_structure)
            parts.append(phase_structure)
        return parts


class MissionStructureBuilder(AbstractStructureBuilder, structure_type="mission"):
    """
    Structure builder for mission definition.

    :param definition: the whole content of definition file
    """

    def _build(self, definition: dict) -> OrderedDict:
        mission_definition = definition[MISSION_DEFINITION_TAG][self.name]
        mission_structure = OrderedDict(deepcopy(mission_definition))

        mission_parts = []
        for part_definition in mission_definition[PARTS_TAG]:
            if ROUTE_TAG in part_definition:
                route_name = part_definition[ROUTE_TAG]
                builder = RouteStructureBuilder(definition, route_name, self.qualified_name)
            elif PHASE_TAG in part_definition:
                phase_name = part_definition[PHASE_TAG]
                builder = PhaseStructureBuilder(definition, phase_name, self.qualified_name)
            elif SEGMENT_TAG in part_definition:
                builder = SegmentStructureBuilder(part_definition, "", self.qualified_name)
            else:
                builder = DefaultStructureBuilder(part_definition, "", self.qualified_name)

            part_structure = {}
            self._insert_builder(builder, part_structure)
            mission_parts.append(part_structure)

        mission_structure[PARTS_TAG] = mission_parts

        return mission_structure

    @property
    def qualified_name(self):
        return self.name


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
        self._structure_builders: Dict[str, AbstractStructureBuilder] = {}
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

        for mission_name in self._definition[MISSION_DEFINITION_TAG]:
            self._structure_builders[mission_name] = MissionStructureBuilder(
                self._definition, mission_name
            )

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
        for input_def in self._structure_builders[mission_name].get_input_definitions():
            input_def.set_variable_value(inputs)
        if mission_name is None:
            mission_name = self.get_unique_mission_name()
        mission = self._build_mission(self._structure_builders[mission_name].structure)
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

        last_part_spec = self._get_mission_part_structures(mission_name)[-1]
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
        for input_def in self._structure_builders[mission_name].get_input_definitions():
            if input_def.variable_name and input_def.variable_name not in input_definition.names():
                input_definition.append(input_def.get_input_definition())

        return input_definition

    def get_unique_mission_name(self) -> str:
        """
        Provides mission name if only one mission is defined in mission file.

        :return: the mission name, if only one mission is defined
        :raise FastMissionFileMissingMissionNameError: if several missions are defined in mission
                                                       file
        """
        if len(self._structure_builders) == 1:
            return list(self._structure_builders.keys())[0]

        raise FastMissionFileMissingMissionNameError(
            "Mission name must be specified if several missions are defined in mission file."
        )

    def get_mission_start_mass_input(self, mission_name: str) -> Optional[str]:
        """

        :param mission_name:
        :return: Target mass variable of first segment, if any.
        """
        part = self._get_first_segment_structure(mission_name)
        if "mass" in part["target"]:
            return part["target"]["mass"].variable_name

    def _get_first_segment_structure(self, mission_name: str):
        part = self._get_mission_part_structures(mission_name)[0]
        while PARTS_TAG in part:
            part = part[PARTS_TAG][0]
        return part

    def get_mission_part_names(self, mission_name: str) -> List[str]:
        """

        :param mission_name:
        :return: list of names of parts (phase or route) for specified mission.
        """
        return [
            part[NAME_TAG]
            for part in self._get_mission_part_structures(mission_name)
            if part.get(TYPE_TAG) in [ROUTE_TAG, PHASE_TAG]
        ]

    def _build_mission(self, mission_structure: OrderedDict) -> FlightSequence:
        """
        Builds mission instance from provided structure.

        :param mission_structure: structure of the mission to build
        :return: the mission instance
        """
        mission = FlightSequence()

        part_kwargs = self._get_part_kwargs({}, mission_structure)

        mission.name = mission_structure[NAME_TAG]
        for part_spec in mission_structure[PARTS_TAG]:
            if TYPE_TAG in part_spec:
                if part_spec[TYPE_TAG] == SEGMENT_TAG:
                    part = self._build_segment(part_spec, part_kwargs)
                if part_spec[TYPE_TAG] == ROUTE_TAG:
                    part = self._build_route(part_spec, part_kwargs)
                elif part_spec[TYPE_TAG] == PHASE_TAG:
                    part = self._build_phase(part_spec, part_kwargs)
                mission.flight_sequence.append(part)
            else:  # reserve definition is used differently
                continue

        return mission

    def _build_route(self, route_structure: OrderedDict, kwargs: Mapping = None):
        """
        Builds route instance.

        :param route_structure: structure of the route to build
        :return: the route instance
        """
        climb_phases = []
        descent_phases = []

        part_kwargs = self._get_part_kwargs(
            kwargs,
            route_structure,
            [
                CLIMB_PARTS_TAG,
                CRUISE_PART_TAG,
                DESCENT_PARTS_TAG,
                "range",
                "distance_accuracy",
            ],
        )

        for part_structure in route_structure[CLIMB_PARTS_TAG]:
            phase = self._build_phase(part_structure, part_kwargs)
            climb_phases.append(phase)

        cruise_phase = self._build_segment(
            route_structure[CRUISE_PART_TAG],
            ChainMap({"target": FlightPoint(ground_distance=0.0)}, part_kwargs),
        )

        for part_structure in route_structure[DESCENT_PARTS_TAG]:
            phase = self._build_phase(part_structure, part_kwargs)
            descent_phases.append(phase)

        if "range" in route_structure:
            flight_range = route_structure["range"].value
            route = RangedRoute(
                climb_phases=climb_phases,
                cruise_segment=cruise_phase,
                descent_phases=descent_phases,
                flight_distance=flight_range,
            )
        else:
            route = FlightSequence()
            route.flight_sequence.extend(climb_phases)

        if "distance_accuracy" in route_structure:
            route.distance_accuracy = route_structure["distance_accuracy"].value

        route.name = route_structure[NAME_TAG]
        return route

    def _build_phase(self, phase_structure: Mapping, kwargs: Mapping = None):
        """
        Builds phase instance

        :param phase_structure: structure of the phase to build
        :return: the phase instance
        """
        phase = FlightSequence(name=phase_structure[NAME_TAG])
        part_kwargs = self._get_part_kwargs(kwargs, phase_structure)

        for part_structure in phase_structure[PARTS_TAG]:
            if part_structure[TYPE_TAG] == PHASE_TAG:
                flight_part = self._build_phase(part_structure, part_kwargs)
            else:
                flight_part = self._build_segment(part_structure, part_kwargs)
            phase.flight_sequence.append(flight_part)

        return phase

    def _build_segment(self, segment_definition: Mapping, kwargs: Mapping) -> FlightSegment:
        """
        Builds a flight segment according to provided definition.

        :param segment_definition: the segment definition from mission file
        :param kwargs: a preset of keyword arguments for FlightSegment instantiation
        :param tag: the expected tag for specifying the segment type
        :return: the FlightSegment instance
        """
        segment_class = SegmentDefinitions.get_segment_class(segment_definition[SEGMENT_TYPE_TAG])
        part_kwargs = kwargs.copy()
        part_kwargs.update(
            {
                name: value
                for name, value in segment_definition.items()
                if name != SEGMENT_TYPE_TAG and name != TYPE_TAG
            }
        )
        part_kwargs.update(self._base_kwargs)
        keys = list(part_kwargs.keys())
        if "polar" in keys:
            polar_dict = {}
            if "ground_effect" in keys:
                polar_dict["ground_effect"] = part_kwargs["ground_effect"]
                #remove field
                del part_kwargs["ground_effect"]
            value = part_kwargs["polar"]
            for kkey, vval in value.items():
                polar_dict[kkey] = vval.value
            value = Polar(polar_dict)
            part_kwargs['polar'] = value

        for key, value in part_kwargs.items():
            if key == "polar":
                value = Polar(value)
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

    def _get_mission_part_structures(self, mission_name: str):
        return self._structure_builders[mission_name].structure[PARTS_TAG]

    def _get_part_kwargs(
        self, kwargs: Mapping, phase_structure: Mapping, specific_exclude: List[str] = None
    ):
        part_kwargs = {}
        if kwargs is not None:
            part_kwargs.update(kwargs)
        if specific_exclude is None:
            specific_exclude = []
        exclude = [NAME_TAG, PARTS_TAG, TYPE_TAG] + specific_exclude
        part_kwargs.update(
            {name: value for name, value in phase_structure.items() if name not in exclude}
        )
        self._replace_input_definitions_by_values(part_kwargs)
        return part_kwargs
