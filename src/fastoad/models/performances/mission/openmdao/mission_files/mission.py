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
from typing import Mapping, Union, Dict, Tuple

import numpy as np
import openmdao.api as om
import pandas as pd
from openmdao.vectors.vector import Vector

from fastoad.base.flight_point import FlightPoint
from fastoad.constants import EngineSetting
from fastoad.models.aerodynamics.constants import POLAR_POINT_COUNT
from fastoad.models.propulsion import IPropulsion
from .schema import (
    PHASE_DEFINITIONS_TAG,
    ROUTE_DEFINITIONS_TAG,
    STEPS_TAG,
    SegmentNames,
    MISSION_DEFINITION_TAG,
    PHASE_TAG,
    SEGMENT_TAG,
    ROUTE_TAG,
    MissionDefinition,
)
from ...base import IFlightPart
from ...flight.base import RangedFlight, SimpleFlight
from ...polar import Polar
from ...segments.base import AbstractSegment
from ....mission.base import FlightSequence

BASE_UNITS = {
    "altitude": "m",
    "true_airspeed": "m/s",
    "equivalent_airspeed": "m/s",
    "range": "m",
    "time": "s",
    "ground_distance": "m",
}


class Mission:
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
        if isinstance(mission_definition, str):
            self._mission_definition = MissionDefinition(mission_definition)
        else:
            self._mission_definition = mission_definition
        self._base_kwargs = {"reference_area": reference_area, "propulsion": propulsion}
        self._name = ""
        self._phases: Dict[str, FlightSequence] = {}
        self._routes: Dict[str, SimpleFlight] = {}
        self._mission: FlightSequence = FlightSequence()

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

    def setup(self, component: om.ExplicitComponent):
        """
        To be used during setup() of provided OpenMDAO component.

        It adds input and output variables deduced from mission definition file.

        :param component: the OpenMDAO component where the setup is done.
        """
        input_definition = {}
        self._identify_inputs(input_definition)
        output_definition = self._identify_outputs()
        output_definition = {
            name: value for name, value in output_definition.items() if name not in input_definition
        }
        for name, units in input_definition.items():
            if name.endswith(":CD") or name.endswith(":CL"):
                component.add_input(name, np.nan, units=units, shape=POLAR_POINT_COUNT)
            else:
                component.add_input(name, np.nan, units=units)

        for name, (units, desc) in output_definition.items():
            component.add_output(name, units=units, desc=desc)

    def compute(
        self, inputs: Vector, outputs: Vector, start_flight_point: FlightPoint
    ) -> pd.DataFrame:
        """
        To be used during compute() of an OpenMDAO component.

        Builds the mission from input file, and computes it. `outputs` vector is
        filled with duration, burned fuel and covered ground distance for each
        part of the flight.

        :param inputs: the input vector of the OpenMDAO component
        :param outputs:  the output vector of the OpenMDAO component
        :param start_flight_point: the starting flight point just after takeoff
        :return: a pandas DataFrame where columns names match
                 :meth:`fastoad.base.flight_point.FlightPoint.get_attribute_keys`
        """
        self._build_phases(inputs)
        self._build_routes(inputs)
        self._build_mission()

        def _compute_vars(name_root, start: FlightPoint, end: FlightPoint):
            """Computes duration, burned fuel and covered distance."""
            if name_root + ":duration" in outputs:
                outputs[name_root + ":duration"] = end.time - start.time
            if name_root + ":fuel" in outputs:
                outputs[name_root + ":fuel"] = start.mass - end.mass
            if name_root + ":distance" in outputs:
                outputs[name_root + ":distance"] = end.ground_distance - start.ground_distance

        if not start_flight_point.name:
            start_flight_point.name = self._mission.flight_sequence[0].name

        current_flight_point = start_flight_point
        flight_points = self._mission.compute_from(start_flight_point)
        for part in self._mission.flight_sequence:
            var_name_root = "data:mission:%s" % part.name
            part_points = flight_points.loc[flight_points.name.str.startswith(part.name)]

            part_end = FlightPoint(part_points.iloc[-1])
            _compute_vars(var_name_root, current_flight_point, part_end)

            if isinstance(part, FlightSequence):
                # In case of a route, outputs are computed for each phase in the route
                phase_start = current_flight_point
                for phase in part.flight_sequence:
                    phase_points = flight_points.loc[flight_points.name == phase.name]
                    if len(phase_points) > 0:
                        phase_end = FlightPoint(phase_points.iloc[-1])
                        var_name_root = "data:mission:%s" % phase.name
                        _compute_vars(var_name_root, phase_start, phase_end)
                        phase_start = phase_end

            current_flight_point = part_end

        # Outputs for the whole mission
        var_name_root = "data:mission:%s" % self._name
        _compute_vars(var_name_root, start_flight_point, current_flight_point)

        return flight_points

    def _identify_inputs(self, input_definition: Dict[str, str], struct=None):
        """
        Identifies the OpenMDAO variables that are provided as parameter values.

        :param input_definition: dictionary to be completed with variable names as keys and units
                                 as values
        :param struct: any part of the mission definition dictionary. If None, the
                       complete mission definition will be used.
        """
        if not struct:
            struct = self._mission_definition

        if isinstance(struct, dict):
            for key, value in struct.items():
                if isinstance(value, str) and ":" in value:
                    input_definition[value] = BASE_UNITS.get(key)
                elif isinstance(value, (dict, list)):
                    self._identify_inputs(input_definition, value)
        elif isinstance(struct, list):
            for value in struct:
                self._identify_inputs(input_definition, value)

    def _identify_outputs(self) -> Dict[str, Tuple[str, str]]:
        """
        Builds names of OpenMDAO outputs from names of mission, route and phases.

        :return: dictionary with variable name as key and unit, description as value
        """
        output_definition = {}

        def _add_vars(mission_name, route_name=None, phase_name=None):
            """
            Feeds output_definition with fuel, duration and distance variables.
            """
            name_root = ":".join(
                name for name in ["data:mission", mission_name, route_name, phase_name] if name
            )
            if route_name and phase_name:
                flight_part_desc = 'phase "%s" of route "%s" in mission "%s"' % (
                    phase_name,
                    route_name,
                    mission_name,
                )
            elif route_name:
                flight_part_desc = 'route "%s" in mission "%s"' % (route_name, mission_name,)
            elif phase_name:
                flight_part_desc = 'phase "%s" in mission "%s"' % (phase_name, mission_name,)
            else:
                flight_part_desc = 'mission "%s"' % (mission_name,)

            output_definition[name_root + ":duration"] = ("s", "duration of %s" % flight_part_desc)
            output_definition[name_root + ":fuel"] = (
                "kg",
                "burned fuel during %s" % flight_part_desc,
            )
            output_definition[name_root + ":distance"] = (
                "m",
                "covered ground distance during %s" % flight_part_desc,
            )

        self._name = self._mission_definition[MISSION_DEFINITION_TAG]["name"]
        _add_vars(self._name)

        for step in self._mission_definition[MISSION_DEFINITION_TAG][STEPS_TAG]:
            if PHASE_TAG in step:
                phase_name = step[PHASE_TAG]
                _add_vars(self._name, phase_name=phase_name)
            else:
                route_name = step[ROUTE_TAG]
                _add_vars(self._name, route_name)
                route_definition = self._mission_definition[ROUTE_DEFINITIONS_TAG][route_name]
                for step_definition in route_definition[STEPS_TAG]:
                    if PHASE_TAG in step_definition:
                        phase_name = step_definition[PHASE_TAG]
                    else:
                        phase_name = "cruise"
                    _add_vars(self._name, route_name, phase_name)

        return output_definition

    def _build_mission(self):
        self._name = self._mission_definition[MISSION_DEFINITION_TAG]["name"]
        self._mission = FlightSequence()
        for part_spec in self._mission_definition[MISSION_DEFINITION_TAG][STEPS_TAG]:
            part_type = "route" if "route" in part_spec else "phase"
            if part_type == "route":
                part = self._routes[part_spec["route"]]
            else:
                part = self._phases[part_spec["phase"]]
            part.name = list(part_spec.values())[0]
            self._mission.flight_sequence.append(part)

        self._set_name(self._mission, self._name)

    def _set_name(self, part: IFlightPart, new_name: str):
        part.name = new_name
        if isinstance(part, FlightSequence):
            for subpart in part.flight_sequence:
                if subpart.name:
                    self._set_name(subpart, ":".join([part.name, subpart.name]))
                else:
                    subpart.name = part.name

    def _build_routes(self, inputs):
        for route_name, definition in self._mission_definition[ROUTE_DEFINITIONS_TAG].items():
            climb_phases = []
            descent_phases = []
            climb = True
            for step_definition in definition[STEPS_TAG]:
                if PHASE_TAG in step_definition:
                    phase = deepcopy(self._phases[step_definition[PHASE_TAG]])
                    if "target" in step_definition:
                        self._parse_target(step_definition["target"])
                        self._replace_by_inputs(step_definition["target"], inputs)
                        phase.flight_sequence[-1] = phase.flight_sequence[-1]
                        phase.flight_sequence[-1].target = FlightPoint(**step_definition["target"])
                    if climb:
                        climb_phases.append(phase)
                    else:
                        descent_phases.append(phase)
                else:
                    # Schema ensures there is one and only one SEGMENT_TAG
                    cruise_phase = self._build_segment(
                        step_definition,
                        {"name": "cruise", "target": FlightPoint(ground_distance=0.0)},
                        inputs,
                    )
                    climb = False

            sequence = SimpleFlight(0.0, climb_phases, cruise_phase, descent_phases)
            sequence.name = route_name
            flight_range = definition["range"]
            if isinstance(flight_range, str):
                flight_range = inputs[definition["range"]]
            self._routes[route_name] = RangedFlight(sequence, flight_range)

    def _build_phases(self, inputs: Mapping):
        for phase_name, definition in self._mission_definition[PHASE_DEFINITIONS_TAG].items():
            phase = FlightSequence()
            kwargs = {name: value for name, value in definition.items() if name != STEPS_TAG}
            phase.name = phase_name

            for step_definition in definition[STEPS_TAG]:
                segment = self._build_segment(step_definition, kwargs, inputs)
                phase.flight_sequence.append(segment)

            self._phases[phase_name] = phase

    def _build_segment(self, step_definition, kwargs, inputs) -> AbstractSegment:
        segment_class = SegmentNames.get_segment_class(step_definition[SEGMENT_TAG])
        step_kwargs = kwargs.copy()
        step_kwargs.update(
            {name: value for name, value in step_definition.items() if name != SEGMENT_TAG}
        )
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
    def _replace_by_inputs(dict_value, inputs):
        for key, value in dict_value.items():
            if isinstance(value, str) and ":" in value:
                dict_value[key] = inputs[value]
