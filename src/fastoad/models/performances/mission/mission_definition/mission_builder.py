"""
Mission generator.
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
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

from copy import deepcopy
from typing import Mapping, Union, Dict, Optional

import openmdao.api as om

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
)
from ..routes import SimpleRoute, RangedRoute

BASE_UNITS = {
    "altitude": "m",
    "true_airspeed": "m/s",
    "equivalent_airspeed": "m/s",
    "range": "m",
    "time": "s",
    "ground_distance": "m",
}


class MissionBuilder:
    """
    This class builds and computes a mission from a provided definition.
    """

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
        if isinstance(mission_definition, str):
            self.definition = MissionDefinition(mission_definition)
        else:
            self.definition = mission_definition
        self._base_kwargs = {"reference_area": reference_area, "propulsion": propulsion}
        self._phases: Dict[str, FlightSequence] = {}
        self._routes: Dict[str, FlightSequence] = {}

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

    def build(self, inputs: Optional[Mapping] = None) -> FlightSequence:
        """
        Builds the flight sequence from definition file
        :param inputs:
        :return:
        """
        self._build_phases(inputs)
        self._build_routes(inputs)
        return self._build_mission()

    def identify_inputs(self, input_definition: Dict[str, str], struct=None):
        """
        Identifies the OpenMDAO variables that are provided as parameter values.

        A value is considered an OpenMDAO variable as soon as it is a string that
        contains a colon ":".

        :param input_definition: dictionary to be completed with variable names as keys and units
                                 as values
        :param struct: any part of the mission definition dictionary. If None, the
                       complete mission definition will be used.
        """
        if struct is None:
            struct = self.definition

        if isinstance(struct, dict):
            for key, value in struct.items():
                if isinstance(value, str) and ":" in value:
                    input_definition[value] = BASE_UNITS.get(key)
                elif isinstance(value, (dict, list)):
                    self.identify_inputs(input_definition, value)
        elif isinstance(struct, list):
            for value in struct:
                self.identify_inputs(input_definition, value)

    def _build_mission(self):
        mission = FlightSequence()

        mission.name = self.definition[MISSION_DEFINITION_TAG]["name"]
        for part_spec in self.definition[MISSION_DEFINITION_TAG][STEPS_TAG]:
            part_type = "route" if "route" in part_spec else "phase"
            if part_type == "route":
                part = self._routes[part_spec["route"]]
            else:
                part = self._phases[part_spec["phase"]]
            part.name = list(part_spec.values())[0]
            mission.flight_sequence.append(part)

        self._propagate_name(mission, mission.name)

        return mission

    def _propagate_name(self, part: IFlightPart, new_name: str):
        part.name = new_name
        if isinstance(part, FlightSequence):
            for subpart in part.flight_sequence:
                if subpart.name:
                    self._propagate_name(subpart, ":".join([part.name, subpart.name]))
                else:
                    subpart.name = part.name

    def _build_routes(self, inputs: Optional[Mapping] = None):
        for route_name, definition in self.definition[ROUTE_DEFINITIONS_TAG].items():
            climb_phases = []
            descent_phases = []
            climb = True
            for step_definition in definition[STEPS_TAG]:
                if PHASE_TAG in step_definition:
                    phase = deepcopy(self._phases[step_definition[PHASE_TAG]])
                    if "target" in step_definition:
                        self._parse_target(step_definition["target"])
                        self._replace_by_inputs(step_definition["target"], inputs)
                        phase.flight_sequence[-1].target = FlightPoint(**step_definition["target"])
                    if climb:
                        climb_phases.append(phase)
                    else:
                        descent_phases.append(phase)
                else:
                    # Schema ensures there is one and only one CRUISE_TYPE_TAG
                    cruise_phase = self._build_segment(
                        step_definition,
                        {"name": "cruise", "target": FlightPoint(ground_distance=0.0)},
                        inputs,
                        tag=CRUISE_TYPE_TAG,
                    )
                    climb = False

            sequence = SimpleRoute(0.0, climb_phases, cruise_phase, descent_phases)
            sequence.name = route_name
            flight_range = definition["range"]
            if isinstance(flight_range, str):
                flight_range = inputs[definition["range"]]
            self._routes[route_name] = RangedRoute(sequence, flight_range)

    def _build_phases(self, inputs: Optional[Mapping] = None):
        for phase_name, definition in self.definition[PHASE_DEFINITIONS_TAG].items():
            phase = FlightSequence()
            kwargs = {name: value for name, value in definition.items() if name != STEPS_TAG}
            phase.name = phase_name

            for step_definition in definition[STEPS_TAG]:
                segment = self._build_segment(step_definition, kwargs, inputs)
                phase.flight_sequence.append(segment)

            self._phases[phase_name] = phase

    def _build_segment(
        self, step_definition, kwargs, inputs: Optional[Mapping], tag=SEGMENT_TAG
    ) -> FlightSegment:
        segment_class = SegmentNames.get_segment_class(step_definition[tag])
        step_kwargs = kwargs.copy()
        step_kwargs.update({name: value for name, value in step_definition.items() if name != tag})
        step_kwargs.update(self._base_kwargs)
        for key, value in step_kwargs.items():
            if key == "polar":
                polar = {}
                for coeff in ["CL", "CD"]:
                    polar[coeff] = value[coeff]
                self._replace_by_inputs(polar, inputs)
                step_kwargs[key] = Polar(polar["CL"], polar["CD"])
            elif key == "target":
                self._parse_target(value)
                self._replace_by_inputs(value, inputs)
                step_kwargs[key] = FlightPoint(**value)
            else:
                step_kwargs[key] = value

        if "engine_setting" in step_kwargs:
            step_kwargs["engine_setting"] = EngineSetting.convert(step_kwargs["engine_setting"])

        self._replace_by_inputs(step_kwargs, inputs)

        segment = segment_class(**step_kwargs)
        return segment

    @staticmethod
    def _parse_target(value):
        for target_key, target_value in value.items():
            if isinstance(target_value, dict) and "value" in target_value:
                value[target_key] = om.convert_units(
                    target_value["value"], target_value.get("unit"), BASE_UNITS.get(target_key),
                )

    @staticmethod
    def _replace_by_inputs(dict_value, inputs: Optional[Mapping]):
        if inputs:
            for key, value in dict_value.items():
                if isinstance(value, str) and value in inputs:
                    dict_value[key] = inputs[value]
