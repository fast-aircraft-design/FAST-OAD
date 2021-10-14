"""
Mission generator.
"""
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

from collections import OrderedDict
from copy import deepcopy
from typing import Dict, List, Mapping, Optional, Tuple, Union

import openmdao.api as om
import pandas as pd

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import IPropulsion
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
        *,
        propulsion: IPropulsion = None,
        reference_area: float = None,
    ):
        """
        This class builds and computes a mission from a provided definition.

        :param mission_definition: as file path or MissionDefinition instance
        :param propulsion: if not provided, the property :attr:`propulsion` must be
                           set before calling :meth:`build`
        :param reference_area: if not provided, the property :attr:`reference_area` must be
                               set before calling :meth:`build`
        """
        super().__init__()
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
        self._parse_values_and_units(self._structure)
        self.get_input_variables(mission_name)  # Needed to process "contextual" variable names
        if mission_name is None:
            mission_name = self.get_unique_mission_name()
        mission = self._build_mission(self._structure[mission_name], inputs)
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
            ref_name = last_part_spec[RESERVE_TAG]["ref"]
            multiplier = last_part_spec[RESERVE_TAG]["multiplier"]

            route_points = flight_points.loc[
                flight_points.name.str.contains("%s:%s" % (mission_name, ref_name))
            ]
            consumed_mass = route_points.mass.iloc[0] - route_points.mass.iloc[-1]
            return consumed_mass * multiplier

        return 0.0

    def get_input_variables(self, mission_name=None) -> Dict[str, str]:
        """
        Identify variables for a defined mission.

        :param mission_name: mission name (can be omitted if only one mission is defined)
        :return: a dict where key, values are names, units.
        """
        if mission_name is None:
            mission_name = self.get_unique_mission_name()

        input_definition = {}
        self._identify_inputs(input_definition, self._structure[mission_name])

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

    def _identify_inputs(
        self,
        input_definition: Dict[str, Tuple[str, str]],
        struct: Union[OrderedDict, list],
        prefix: str = None,
    ):
        """
        Identifies the OpenMDAO variables that are provided as parameter values.

        A value is considered an OpenMDAO variable as soon as it is a string that
        contains a colon ":".

        If a value starts with a tilde "~<some_name>", it will be considered contextual and the
        actual name will be built as
        "data:mission:<mission_name>:<route_name>:<phase_name>:<some_name>" (route and phase names
        will be used only if applicable). The variable name in provided structure will be modified
        accordingly.
        If value is simply "~", the parameter name will be used.

        :param input_definition: dictionary to be completed with variable names as keys and
                                 (units, description) as values
        :param struct: any part of the structure dictionary.
        :param prefix:

        """
        if prefix is None:
            prefix = "data:mission"

        if isinstance(struct, dict):
            for key, value in struct.items():
                name = struct.get("mission", "") + struct.get("route", "") + struct.get("phase", "")
                prefix_addition = ":" + name if name else ""

                if isinstance(value, str) and value.startswith("~") or value is None:
                    # "~" alone is interpreted as "null" by the yaml parser
                    # In that case, the parameter name in the mission file is used as suffix.
                    # Otherwise, the string after the "~" is used as suffix.
                    suffix = key if value is None else value[1:]
                    value = prefix + prefix_addition + ":" + suffix
                if isinstance(value, str) and ":" in value:
                    input_definition[value] = (BASE_UNITS.get(key), "Input defined by the mission.")
                    struct[key] = value
                elif isinstance(value, (dict, list)):
                    self._identify_inputs(input_definition, value, prefix + prefix_addition)

        elif isinstance(struct, list):
            for value in struct:
                self._identify_inputs(input_definition, value, prefix)

    def _build_mission(
        self, mission_structure: OrderedDict, inputs: Optional[Mapping] = None
    ) -> FlightSequence:
        """
        Builds mission instance from provided structure.

        :param mission_structure: structure of the mission to build
        :param inputs: if provided, variable inputs will be replaced by their value.
        :return: the mission instance
        """
        mission = FlightSequence()

        mission.name = mission_structure["mission"]
        for part_spec in mission_structure[PARTS_TAG]:
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

        for part_structure in route_structure[CLIMB_PARTS_TAG]:
            phase = self._build_phase(part_structure, inputs)
            climb_phases.append(phase)
            phase.name = list(part_structure.values())[0]

        cruise_phase = self._build_segment(
            route_structure[CRUISE_PART_TAG],
            {"name": "cruise", "target": FlightPoint(ground_distance=0.0)},
            inputs,
        )
        cruise_phase.name = "cruise"

        for part_structure in route_structure[DESCENT_PARTS_TAG]:
            phase = self._build_phase(part_structure, inputs)
            descent_phases.append(phase)
            phase.name = list(part_structure.values())[0]

        if "range" in route_structure:
            flight_range = route_structure["range"]
            if isinstance(flight_range, str):
                flight_range = inputs[route_structure["range"]]
            route = RangedRoute(
                climb_phases, cruise_phase, descent_phases, flight_distance=flight_range
            )
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
        kwargs = {name: value for name, value in phase_structure.items() if name != PARTS_TAG}
        del kwargs[PHASE_TAG]

        for part_structure in phase_structure[PARTS_TAG]:
            segment = self._build_segment(part_structure, kwargs, inputs)
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
        segment_class = SegmentDefinitions.get_segment_class(segment_definition[tag])
        part_kwargs = kwargs.copy()
        part_kwargs.update(
            {name: value for name, value in segment_definition.items() if name != tag}
        )
        part_kwargs.update(self._base_kwargs)
        for key, value in part_kwargs.items():
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

            part_kwargs[key] = value

        if "engine_setting" in part_kwargs:
            part_kwargs["engine_setting"] = EngineSetting.convert(part_kwargs["engine_setting"])

        self._replace_by_inputs(part_kwargs, inputs)

        segment = segment_class(**part_kwargs)
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
                        value["value"], value.get("unit"), BASE_UNITS.get(key)
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
