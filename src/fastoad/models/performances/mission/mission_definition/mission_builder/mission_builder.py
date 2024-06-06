"""Mission generator."""
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

from collections import ChainMap
from copy import deepcopy
from dataclasses import fields
from os import PathLike
from typing import Dict, List, Mapping, Optional, Union

import pandas as pd

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import IPropulsion
from fastoad.openmdao.variables import VariableList
from .constants import NAME_TAG, SEGMENT_TYPE_TAG, TYPE_TAG
from .input_definition import InputDefinition
from .structure_builders import (
    AbstractStructureBuilder,
    MissionStructureBuilder,
    PhaseStructureBuilder,
)
from ..exceptions import FastMissionFileMissingMissionNameError
from ..schema import (
    CLIMB_PARTS_TAG,
    CRUISE_PART_TAG,
    DESCENT_PARTS_TAG,
    MISSION_DEFINITION_TAG,
    MissionDefinition,
    PARTS_TAG,
    PHASE_TAG,
    POLAR_TAG,
    RESERVE_TAG,
    ROUTE_TAG,
    SEGMENT_TAG,
)
from ...base import FlightSequence
from ...mission import Mission
from ...polar import Polar
from ...polar_modifier import RegisterPolarModifier, UnchangedPolar
from ...routes import RangedRoute
from ...segments.base import AbstractFlightSegment, RegisterSegment


# Rationale:
# The way we parse the mission definition file answers several needs:
# - Producing an executable mission instance, able to compute the mission simulation.
# - Allowing to replace variables in the mission definition by their values, knowing the
#   name can be contextual: a same phase definition can be used in 2 different routes or missions
#   and variable names in this phase may depend on the parent.
# - Allowing to know all the needed variables before knowing their values, hence before
#   building the mission instance.
#
# Therefore, we have first the structure_builders package, that will provide classes to parse the
# definition file to create a global structure of the mission, ready to implement. This structure
# will be able to provide the actual names of the variables used in the mission, but does not
# have to know their values.
#
# Then we can use the MissionBuilder below to build the mission instance and provide information
# on the mission, once variable values have been supplied.


class MissionBuilder:
    """
    This class builds and computes a mission from a provided definition.
    """

    def __init__(
        self,
        mission_definition: Union[str, PathLike, MissionDefinition],
        *,
        propulsion: IPropulsion = None,
        reference_area: float = None,
        mission_name: Optional[str] = None,
        variable_prefix: str = "data:mission",
    ):
        """
        :param mission_definition: a file path or MissionDefinition instance
        :param propulsion: if not provided, the property :attr:`propulsion` must be
                           set before calling :meth:`build`
        :param reference_area: if not provided, the property :attr:`reference_area` must be
                               set before calling :meth:`build`
        :param mission_name: name of chosen mission, if already decided.
        :param variable_prefix: prefix for auto-generated variable names.
        """
        self._structure_builders: Dict[str, AbstractStructureBuilder] = {}

        self._variable_prefix: str = variable_prefix

        #: The definition of missions as provided in input file.
        self.definition: MissionDefinition = mission_definition

        self._mission_name = mission_name

        self._base_kwargs = {"reference_area": reference_area, "propulsion": propulsion}

    @property
    def definition(self) -> MissionDefinition:
        """
        The mission definition instance.

        If it is set as a file path, then the matching file will be read and interpreted.
        """
        return self._definition

    @definition.setter
    def definition(self, mission_definition: Union[str, PathLike, MissionDefinition]):
        if isinstance(mission_definition, MissionDefinition):
            self._definition = mission_definition
        else:
            self._definition = MissionDefinition(mission_definition)

        self._update_structure_builders()

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

    @property
    def mission_name(self):
        """The mission name, in case it has been specified, or if it is unique in the file."""
        if self._mission_name is None:
            self._mission_name = self.get_unique_mission_name()

        return self._mission_name

    @mission_name.setter
    def mission_name(self, value):
        if value is None:
            self._mission_name = None
        elif value in self.definition[MISSION_DEFINITION_TAG]:
            self._mission_name = value
        else:
            raise FastMissionFileMissingMissionNameError(
                f'No Mission named "{value}" in provided mission file.'
            )

    @property
    def variable_prefix(self):
        """The prefix for auto-generated variable names."""
        return self._variable_prefix

    @variable_prefix.setter
    def variable_prefix(self, value):
        self._variable_prefix = value
        self._update_structure_builders()

    def build(self, inputs: Optional[Mapping] = None, mission_name: str = None) -> Mission:
        """
        Builds the flight sequence from definition file.

        :param inputs: if provided, any input parameter that is a string which matches
                       a key of `inputs` will be replaced by the corresponding value
        :param mission_name: mission name (can be omitted if only one mission is defined or if
                             :attr:`mission` has been defined)
        :return:
        """
        if mission_name is None:
            mission_name = self.mission_name

        if self.get_input_weight_variable_name(mission_name) is None:
            self._add_default_taxi_takeoff(mission_name)

        for input_def in self._structure_builders[mission_name].get_input_definitions():
            input_def.set_variable_value(inputs)

        mission = self._build_mission(self._structure_builders[mission_name].structure)
        return mission

    def get_route_names(self, mission_name: str = None) -> List[str]:
        """

        :param mission_name:
        :return: a list with names of all routes in the mission, in order.
        """
        if mission_name is None:
            mission_name = self.mission_name

        mission_parts = self.definition[MISSION_DEFINITION_TAG][mission_name][PARTS_TAG]
        route_names = [part[ROUTE_TAG] for part in mission_parts if ROUTE_TAG in part]

        return route_names

    def get_route_ranges(
        self, inputs: Optional[Mapping] = None, mission_name: str = None
    ) -> List[float]:
        """

        :param inputs: if provided, any input parameter that is a string which matches
                       a key of `inputs` will be replaced by the corresponding value
        :param mission_name: mission name (can be omitted if only one mission is defined or if
                             :attr:`mission` has been defined)
        :return: list of flight ranges for each element of the flight sequence that is a route
        """
        if mission_name is None:
            mission_name = self.mission_name

        routes = self.build(inputs, mission_name)
        return [route.flight_distance for route in routes if isinstance(route, RangedRoute)]

    def get_reserve(self, flight_points: pd.DataFrame, mission_name: str = None) -> float:
        """
        Computes the reserve fuel according to definition in mission input file.

        :param flight_points: the dataframe returned by compute_from() method of the
                              instance returned by :meth:`build`
        :param mission_name: mission name (can be omitted if only one mission is defined or if
                             :attr:`mission` has been defined)
        :return: the reserve fuel mass in kg, or 0.0 if no reserve is defined.
        """

        if mission_name is None:
            mission_name = self.mission_name

        last_part_spec = self._get_mission_part_structures(mission_name)[-1]
        if RESERVE_TAG in last_part_spec:
            ref_name = last_part_spec[RESERVE_TAG]["ref"].value
            multiplier = last_part_spec[RESERVE_TAG]["multiplier"].value

            route_points = flight_points.loc[
                flight_points.name.str.contains(f"{mission_name}:{ref_name}")
            ]
            consumed_mass = route_points.mass.iloc[0] - route_points.mass.iloc[-1]
            return consumed_mass * multiplier

        return 0.0

    def get_input_variables(self, mission_name=None) -> VariableList:
        """
        Identify variables for a defined mission.

        :param mission_name: mission name (can be omitted if only one mission is defined or if
                             :attr:`mission` has been defined)
        :return: a VariableList instance.
        """
        if mission_name is None:
            mission_name = self.mission_name

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

    def get_input_weight_variable_name(self, mission_name: str = None) -> Optional[str]:
        """
        Search the mission structure for a segment that has a target absolute mass defined and
        returns the associated variable name.

        :param mission_name: mission name (can be omitted if only one mission is defined or if
                             :attr:`mission` has been defined)
        :return: The variable name, or None if no target mass found.
        """

        return self._get_input_weight_variable_name_in_structure(
            self._get_mission_part_structures(mission_name)
        )

    def _update_structure_builders(self):
        for mission_name in self._definition[MISSION_DEFINITION_TAG]:
            self._structure_builders[mission_name] = MissionStructureBuilder(
                self._definition, mission_name, variable_prefix=self._variable_prefix
            )

            if self.get_input_weight_variable_name(mission_name) is None:
                self._add_default_taxi_takeoff(mission_name)

    def _build_mission(self, mission_structure: dict) -> Mission:
        """
        Builds mission instance from provided structure.

        :param mission_structure: structure of the mission to build
        :return: the mission instance
        """

        part_kwargs = self._get_part_kwargs({}, mission_structure)

        mission = Mission(target_fuel_consumption=part_kwargs.get("target_fuel_consumption"))

        mission.name = mission_structure[NAME_TAG]
        for part_spec in mission_structure[PARTS_TAG]:
            if TYPE_TAG not in part_spec:
                continue
            if part_spec[TYPE_TAG] == SEGMENT_TAG:
                part = self._build_segment(part_spec, part_kwargs)
            elif part_spec[TYPE_TAG] == ROUTE_TAG:
                part = self._build_route(part_spec, part_kwargs)
            elif part_spec[TYPE_TAG] == PHASE_TAG:
                part = self._build_phase(part_spec, part_kwargs)
            else:
                raise RuntimeError(
                    "Unknown part type. This error should have been prevented "
                    "by the JSON schema validation."
                )
            mission.append(part)

        last_part = mission_structure[PARTS_TAG][-1]
        if RESERVE_TAG in last_part:
            mission.reserve_ratio = last_part[RESERVE_TAG]["multiplier"].value
            base_route_name_definition = last_part[RESERVE_TAG].get("ref")
            if base_route_name_definition:
                mission.reserve_base_route_name = (
                    f"{mission.name}:{base_route_name_definition.value}"
                )

        return mission

    def _build_route(self, route_structure: dict, kwargs: Mapping = None):
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
            phase.append(flight_part)

        return phase

    def _build_segment(self, segment_definition: Mapping, kwargs: dict) -> AbstractFlightSegment:
        """
        Builds a flight segment according to provided definition.

        :param segment_definition: the segment definition from mission file
        :param kwargs: a preset of keyword arguments for AbstractFlightSegment instantiation
        :return: the FlightSegment instance
        """
        segment_class = RegisterSegment.get_class(segment_definition[SEGMENT_TYPE_TAG])
        part_kwargs = kwargs.copy()
        part_kwargs.update(segment_definition)
        part_kwargs.update(self._base_kwargs)
        part_kwargs["polar_modifier"] = UnchangedPolar()
        for key, value in part_kwargs.items():
            if key == POLAR_TAG:
                modifier_kwargs = deepcopy(value.get("modifier"))
                value = Polar(
                    cl=value["CL"].value,
                    cd=value["CD"].value,
                    alpha=value["alpha"].value if "alpha" in value else None,
                )
                if modifier_kwargs:
                    if isinstance(modifier_kwargs, InputDefinition):
                        modifier_kwargs = {NAME_TAG: modifier_kwargs.value}
                    modifier_class = RegisterPolarModifier.get_class(modifier_kwargs[NAME_TAG])
                    del modifier_kwargs[NAME_TAG]
                    self._replace_input_definitions_by_values(modifier_kwargs)
                    part_kwargs["polar_modifier"] = modifier_class(**modifier_kwargs)
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

        input_field_names = [
            class_field.name for class_field in fields(segment_class) if class_field.init
        ]
        part_kwargs = {key: value for key, value in part_kwargs.items() if key in input_field_names}
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

    def _get_input_weight_variable_name_in_structure(
        self, structure: Union[list, dict]
    ) -> Optional[str]:
        for tag in [PARTS_TAG, CLIMB_PARTS_TAG, DESCENT_PARTS_TAG]:
            if tag in structure:
                return self._get_input_weight_variable_name_in_structure(structure[tag])

        if isinstance(structure, list):
            for item in structure:
                result = self._get_input_weight_variable_name_in_structure(item)
                if result:
                    return result

        if "target" in structure and "mass" in structure["target"]:
            target_mass = structure["target"]["mass"]
            if not target_mass.is_relative:
                name = target_mass.variable_name
                if name:
                    return name

        return None

    def _add_default_taxi_takeoff(self, mission_name):
        definition = {
            "phases": {
                "taxi_out": {
                    "parts": [
                        {
                            "segment": "start",
                            "target": {
                                "altitude": {"value": "~", "unit": "ft", "default": 0.0},
                                "true_airspeed": {"value": "~", "unit": "m/s", "default": 0.0},
                            },
                        },
                        {
                            "segment": "taxi",
                            "time_step": {
                                "value": "settings:mission~",
                                "default": 60.0,
                                "unit": "s",
                            },
                            "thrust_rate": "~",
                            "true_airspeed": {"value": "~", "unit": "m/s", "default": 0.0},
                            "target": {"time": "~duration"},
                        },
                    ],
                },
                "takeoff": {
                    "parts": [
                        {
                            "segment": "transition",
                            "target": {
                                "delta_altitude": {
                                    "value": "~safety_altitude",
                                    "unit": "ft",
                                    "default": 35.0,
                                },
                                "delta_mass": {"value": "-~fuel", "unit": "kg"},
                                "time": {"value": "~duration", "default": 0.0, "unit": "s"},
                                "true_airspeed": {"value": "~V2", "unit": "m/s"},
                            },
                        },
                        {
                            "segment": "mass_input",
                            "target": {"mass": {"value": "~~:TOW", "unit": "kg"}},
                        },
                    ]
                },
            }
        }

        taxi_out = PhaseStructureBuilder(
            definition, "taxi_out", mission_name, self._variable_prefix
        )
        taxi_out_structure = self._structure_builders[mission_name].process_builder(taxi_out)
        self._structure_builders[mission_name].structure[PARTS_TAG].insert(0, taxi_out_structure)

        takeoff = PhaseStructureBuilder(definition, "takeoff", mission_name, self._variable_prefix)
        takeoff_structure = self._structure_builders[mission_name].process_builder(takeoff)
        self._structure_builders[mission_name].structure[PARTS_TAG].insert(1, takeoff_structure)
