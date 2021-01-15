"""
Mission generator.
"""
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
from collections import OrderedDict
from copy import deepcopy
from typing import Mapping, Union, Dict, Optional, List, Tuple

import openmdao.api as om
import pandas as pd

from fastoad.base.flight_point import FlightPoint
from fastoad.constants import EngineSetting
from fastoad.models.performances.mission.base import FlightSequence
from fastoad.models.performances.mission.base import IFlightPart
from fastoad.models.performances.mission.polar import Polar
from fastoad.models.performances.mission.segments.base import FlightSegment
from fastoad.models.propulsion import IPropulsion
from .schema import (
    PHASE_DEFINITIONS_TAG,
    ROUTE_DEFINITIONS_TAG,
    MISSION_DEFINITION_TAG,
    STEPS_TAG,
    PHASE_TAG,
    SEGMENT_TAG,
    CRUISE_TYPE_TAG,
    SegmentNames,
    MissionDefinition,
    RESERVE_TAG,
)
from ..routes import RangedRoute

BASE_UNITS = {
    "altitude": "m",
    "true_airspeed": "m/s",
    "equivalent_airspeed": "m/s",
    "range": "m",
    "time": "s",
    "ground_distance": "m",
}


class MissionBuilder:
    def __init__(
        self,
        mission_definition: Union[str, MissionDefinition],
        propulsion: IPropulsion = None,
        reference_area: float = None,
    ):
        """
        This class builds and computes a mission from a provided definition.

        :param mission_definition: as file path or MissionDefinition instance
        :param propulsion: if not provided, the property :attr:`propulsion` must be
                           set before calling :meth:`compute`
        :param reference_area: if not provided, the property :attr:`reference_area` must be
                               set before calling :meth:`compute`
        """
        super().__init__()
        self.definition = mission_definition
        self._base_kwargs = {"reference_area": reference_area, "propulsion": propulsion}

    @property
    def definition(self) -> MissionDefinition:
        return self._definition

    @definition.setter
    def definition(
        self, mission_definition: Union[str, MissionDefinition],
    ):
        if isinstance(mission_definition, str):
            self._definition = MissionDefinition(mission_definition)
        else:
            self._definition = mission_definition

        self._structure = self._build_mission_structure()
        self._input_definition = {}
        self._identify_inputs(self.input_definition, self._structure, "data:mission")

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
    def mission_name(self) -> str:
        """The mission name as defined in input file."""
        return self.definition[MISSION_DEFINITION_TAG]["name"]

    @property
    def input_definition(self) -> Dict[str, str]:
        """
        The variable inputs in mission definition as a dict where key, values are
        names, units.
        """
        return self._input_definition

    def build(self, inputs: Optional[Mapping] = None) -> FlightSequence:
        """
        Builds the flight sequence from definition file.

        :param inputs: if provided, any input parameter that is a string which matches
                       a key of `inputs` will be replaced by the corresponding value
        :return:
        """
        self._parse_values_and_units(self._structure)
        mission = self._build_mission(self._structure, inputs)
        self._propagate_name(mission, mission.name)
        return mission

    def get_route_ranges(self, inputs: Optional[Mapping] = None) -> List[float]:
        """

        :param inputs: if provided, any input parameter that is a string which matches
                       a key of `inputs` will be replaced by the corresponding value
        :return: list of flight ranges for each element of the flight sequence that is a route
        """
        routes = self.build(inputs).flight_sequence
        return [route.flight_distance for route in routes if isinstance(route, RangedRoute)]

    def get_route_cruise_speeds(self, inputs: Optional[Mapping] = None) -> List[Tuple[str, float]]:
        """
        Determines the cruise speed for each route in the flight sequence.

        Each result of the list is a tuple where the first element is the parameter name
        (mach, true_airspeed, equivalent_airspeed) and the second one is the value.

        :param inputs: if provided, any input parameter that is a string which matches
                       a key of `inputs` will be replaced by the corresponding value
        :return: list of cruise speed definitions for each element of the flight sequence that is
                 a route
        """
        routes = self.build(inputs).flight_sequence
        return [route.cruise_speed for route in routes if isinstance(route, RangedRoute)]

    def get_reserve(self, flight_points: pd.DataFrame) -> float:
        """
        Computes the reserve fuel according to definition in mission input file.

        :param flight_points: the dataframe returned by compute_from() method of the
                              instance returned by :meth:`build`
        :return: the reserve fuel mass in kg, or 0.0 if no reserve is defined.
        """

        last_part_spec = self.definition[MISSION_DEFINITION_TAG][STEPS_TAG][-1]
        if RESERVE_TAG in last_part_spec:
            ref_name = last_part_spec[RESERVE_TAG]["ref"]
            multiplier = last_part_spec[RESERVE_TAG]["multiplier"]

            route_points = flight_points.loc[
                flight_points.name.str.contains("%s:%s" % (self.mission_name, ref_name))
            ]
            consumed_mass = route_points.mass.iloc[0] - route_points.mass.iloc[-1]
            return consumed_mass * multiplier

        return 0.0

    def _build_mission_structure(self):
        structure = OrderedDict()
        structure.update(deepcopy(self.definition[MISSION_DEFINITION_TAG]))
        mission_parts = []
        for part_definition in self.definition[MISSION_DEFINITION_TAG][STEPS_TAG]:
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

        structure[STEPS_TAG] = mission_parts
        return structure

    def _build_route_structure(self, route_definition):
        route_structure = OrderedDict()
        route_structure.update(deepcopy(route_definition))
        route_parts = []
        for part_definition in route_definition[STEPS_TAG]:
            if "phase" in part_definition:
                phase_name = part_definition["phase"]
                phase_structure = OrderedDict({"phase": phase_name})
                phase_structure.update(deepcopy(self.definition[PHASE_DEFINITIONS_TAG][phase_name]))
                route_parts.append(phase_structure)
            else:
                route_parts.append(part_definition)

        route_structure[STEPS_TAG] = route_parts
        return route_structure

    def _identify_inputs(self, input_definition: Dict[str, str], struct=None, prefix=None):
        """
        Identifies the OpenMDAO variables that are provided as parameter values.

        A value is considered an OpenMDAO variable as soon as it is a string that
        contains a colon ":".

        If a value starts with a colon ":<some_name>", it will be considered contextual and the
        actual name will be built as
        "data:mission:<mission_name>:<route_name>:<phase_name>:<some_name>" (route and phase names
        will be used only if applicable).

        :param input_definition: dictionary to be completed with variable names as keys and units
                                 as values
        :param struct: any part of the mission definition dictionary. If None, the
                       complete mission definition will be used.
        """
        if struct is None:
            struct = self._structure

        if isinstance(struct, dict):
            for key, value in struct.items():
                if isinstance(value, str) and ":" in value:
                    if value.startswith(":"):
                        value = prefix + value
                    input_definition[value] = BASE_UNITS.get(key)
                elif isinstance(value, (dict, list)):
                    name = (
                        struct.get("name", "") + struct.get("route", "") + struct.get("phase", "")
                    )
                    prefix_addition = ":" + name if name else ""
                    self._identify_inputs(input_definition, value, prefix + prefix_addition)

        elif isinstance(struct, list):
            for value in struct:
                self._identify_inputs(input_definition, value, prefix)

    def _build_mission(
        self, mission_structure: OrderedDict, inputs: Optional[Mapping] = None
    ) -> FlightSequence:
        """
        Builds mission instance from self._structure

        :param mission_structure: structure of the mission to build
        :param inputs: if provided, variable inputs will be replaced by their value.
        :return: the mission instance
        """
        mission = FlightSequence()

        mission.name = self.mission_name
        for part_spec in mission_structure[STEPS_TAG]:
            if "route" in part_spec:
                part = self._build_route(part_spec, inputs)
            elif "phase" in part_spec:
                part = self._build_phase(part_spec, inputs)
            elif "segment" in part_spec:
                part = self._build_segment(part_spec, {}, inputs)
            else:  # reserve definition is used differently
                continue
            part.name = list(part_spec.values())[0]
            mission.flight_sequence.append(part)

        return mission

    def _build_route(self, route_structure: OrderedDict, inputs: Optional[Mapping] = None):
        """
        Builds route instance.

        :param route_structure: structure of the route to build
        :param inputs: if provided, variable inputs will be replaced by their value.
        :return: the route instance
        """
        climb_phases = []
        descent_phases = []
        climb = True
        for step_structure in route_structure[STEPS_TAG]:
            if PHASE_TAG in step_structure:
                phase = self._build_phase(step_structure, inputs)
                if climb:
                    climb_phases.append(phase)
                else:
                    descent_phases.append(phase)
                phase.name = list(step_structure.values())[0]
            else:
                # Schema ensures there is one and only one CRUISE_TYPE_TAG
                cruise_phase = self._build_segment(
                    step_structure,
                    {"name": "cruise", "target": FlightPoint(ground_distance=0.0)},
                    inputs,
                    tag=CRUISE_TYPE_TAG,
                )
                cruise_phase.name = "cruise"
                climb = False

        if "range" in route_structure:
            flight_range = route_structure["range"]
            if isinstance(flight_range, str):
                flight_range = inputs[route_structure["range"]]
            route = RangedRoute(climb_phases, cruise_phase, descent_phases, flight_range)
        else:
            route = FlightSequence()
            route.flight_sequence.extend(climb_phases)

        return route

    def _build_phase(self, phase_structure, inputs: Optional[Mapping] = None):
        """
        Builds phase instance

        :param phase_structure: structure of the phase to build
        :param inputs: if provided, variable inputs will be replaced by their value.
        :return: the phase instance
        """
        phase = FlightSequence()
        kwargs = {name: value for name, value in phase_structure.items() if name != STEPS_TAG}
        del kwargs[PHASE_TAG]

        for step_structure in phase_structure[STEPS_TAG]:
            segment = self._build_segment(step_structure, kwargs, inputs)
            phase.flight_sequence.append(segment)

        return phase

    def _build_segment(
        self, segment_definition: dict, kwargs: dict, inputs: Optional[Mapping], tag=SEGMENT_TAG
    ) -> FlightSegment:
        """
        Builds a flight segment according to provided definition.

        :param segment_definition: the segment definition from mission file
        :param kwargs: a preset of keyword arguments for FlightSegment instantiation
        :param inputs: if provided, any input parameter that is a string which matches
                       a key of `inputs` will be replaced by the corresponding value
        :param tag: the expected tag for specifying the segment type
        :return: the FlightSegment instance
        """
        segment_class = SegmentNames.get_segment_class(segment_definition[tag])
        step_kwargs = kwargs.copy()
        step_kwargs.update(
            {name: value for name, value in segment_definition.items() if name != tag}
        )
        step_kwargs.update(self._base_kwargs)
        for key, value in step_kwargs.items():
            if key == "polar":
                polar = {}
                for coeff in ["CL", "CD"]:
                    polar[coeff] = value[coeff]
                self._replace_by_inputs(polar, inputs)
                value = Polar(polar["CL"], polar["CD"])
            elif key == "target":
                if not isinstance(value, FlightPoint):
                    self._replace_by_inputs(value, inputs)
                    value = FlightPoint(**value)

            step_kwargs[key] = value

        if "engine_setting" in step_kwargs:
            step_kwargs["engine_setting"] = EngineSetting.convert(step_kwargs["engine_setting"])

        self._replace_by_inputs(step_kwargs, inputs)

        segment = segment_class(**step_kwargs)
        return segment

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
                    self._propagate_name(subpart, ":".join([part.name, subpart.name]))
                else:
                    subpart.name = part.name

    @classmethod
    def _parse_values_and_units(cls, definition):
        """
        Browse recursively provided dictionary and if a dictionary that has
        "value" and "unit" as only keys is found, it is transformed into a
        value in base units, as defined in BASE_UNITS.

        Does nothing if definition is not a dict.

        :param definition:
        """

        if isinstance(definition, dict):
            for key, value in definition.items():
                if isinstance(value, dict) and "value" in value.keys():
                    definition[key] = om.convert_units(
                        value["value"], value.get("unit"), BASE_UNITS.get(key),
                    )
                else:
                    cls._parse_values_and_units(value)
        elif isinstance(definition, list):
            for value in definition:
                cls._parse_values_and_units(value)

    @staticmethod
    def _replace_by_inputs(parameter_definition: dict, inputs: Optional[Mapping]):
        """
        In provided dict, if a value is a string that matches a key of `inputs`, replaces
        it by the value provided in `inputs`.

        :param parameter_definition:
        :param inputs:
        """
        if inputs:
            for key, value in parameter_definition.items():
                if isinstance(value, str) and value in inputs:
                    parameter_definition[key] = inputs[value]
