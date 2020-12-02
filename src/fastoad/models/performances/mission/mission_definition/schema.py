"""
Schema for mission definition files.
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
from dataclasses import fields
from enum import Enum
from os import PathLike
from typing import Union, Set

from ensure import Ensure
from strictyaml import (
    load,
    Map,
    MapPattern,
    Optional,
    Str,
    Float,
    Bool,
    Seq,
    Any,
    YAML,
    CommaSeparated,
)

from fastoad.base.flight_point import FlightPoint
from ..segments.altitude_change import AltitudeChangeSegment
from ..segments.cruise import (
    OptimalCruiseSegment,
    ClimbAndCruiseSegment,
    BreguetCruiseSegment,
)
from ..segments.hold import HoldSegment
from ..segments.speed_change import SpeedChangeSegment
from ..segments.taxi import TaxiSegment
from ..segments.transition import DummyTransitionSegment

# Tags
SEGMENT_TAG = "segment"
ROUTE_TAG = "route"
PHASE_TAG = "phase"
CRUISE_TYPE_TAG = "cruise_type"
STEPS_TAG = "steps"
MISSION_DEFINITION_TAG = "mission"
ROUTE_DEFINITIONS_TAG = "route_definitions"
PHASE_DEFINITIONS_TAG = "phase_definitions"
POLAR_TAG = "polar"


class MissionDefinition(dict):
    def __init__(self, file_path: Union[str, PathLike] = None):
        """
        Class for reading a mission definition from a YAML file.

        Path of YAML file should be provided at instantiation, or in
        :meth:`load`.

        :param file_path: path of YAML file to read.
        """
        super().__init__()
        if file_path:
            self.load(file_path)

    def load(self, file_path: Union[str, PathLike]):
        """
        Loads a mission definition from provided file path.

        Any existing definition will be overwritten.

        :param file_path: path of YAML file to read.
        """
        self.clear()
        with open(file_path) as yaml_file:
            content = load(yaml_file.read(), self._get_schema())

        self._validate(content)
        self.update(content.data)

    @classmethod
    def _validate(cls, content: YAML):
        """
        Does a second pass validation of file content.

        Also applies this feature:
                - polar: foo:bar
            is translated to:
                - polar:
                    CL: foo:bar:CL
                    CD: foo:bar:CD

        Errors are raised if file content is incorrect.

        :param content:
        """
        step_names = set(content[PHASE_DEFINITIONS_TAG].keys())

        for phase_definition in content[PHASE_DEFINITIONS_TAG].values():
            cls._process_polar_definition(phase_definition)
            for segment_definition in phase_definition[STEPS_TAG]:
                cls._process_polar_definition(segment_definition)

        for route_definition in content[ROUTE_DEFINITIONS_TAG].values():
            # Routes are expected to contain some phases and ONE cruise phase
            cruise_step_count = 0
            for step in route_definition[STEPS_TAG]:
                cls._process_polar_definition(step)
                Ensure(step.keys()).contains_one_of([PHASE_TAG, CRUISE_TYPE_TAG])

                if PHASE_TAG in step:
                    Ensure(step[PHASE_TAG]).is_in(step_names)
                    YAML(step).revalidate(Map(cls._get_phase_in_route_mapping()))
                else:  # CRUISE_TYPE_TAG in step
                    cruise_step_count += 1
                    YAML(step).revalidate(Map(cls._get_segment_mapping(CRUISE_TYPE_TAG)))
            Ensure(cruise_step_count).is_less_than_or_equal_to(1)

        for step in content[MISSION_DEFINITION_TAG][STEPS_TAG]:
            step_type, step_name = tuple(*step.items())
            if step_type == PHASE_TAG:
                Ensure(step_name).is_in(content[PHASE_DEFINITIONS_TAG].keys())
            elif step_type == ROUTE_TAG:
                Ensure(step_name).is_in(content[ROUTE_DEFINITIONS_TAG].keys())

    @staticmethod
    def _process_polar_definition(struct: YAML):
        """
        If "foo:bar:baz" is provided as value for the "polar" key in provided dictionary, it is
        replaced by the dict {"CL":"foo:bar:baz:CL", "CD":"foo:bar:baz:CD"}
        """
        if POLAR_TAG in struct:
            polar_def = struct[POLAR_TAG].value
            if isinstance(polar_def, str) and ":" in polar_def:
                struct[POLAR_TAG] = OrderedDict({"CL": polar_def + ":CL", "CD": polar_def + ":CD"})

    @classmethod
    def _get_schema(cls):
        return Map(
            {
                PHASE_DEFINITIONS_TAG: MapPattern(Str(), Map(cls._get_phase_mapping())),
                ROUTE_DEFINITIONS_TAG: MapPattern(Str(), Map(cls._get_route_mapping())),
                MISSION_DEFINITION_TAG: Map(cls._get_mission_mapping()),
            }
        )

    @classmethod
    def _get_target_schema(cls) -> Map:
        target_schema_map = {}
        for key in [f.name for f in fields(FlightPoint)]:
            target_schema_map[Optional(key, default=None)] = cls._get_dimensioned_value_mapping()
        return Map(target_schema_map)

    @classmethod
    def _get_base_step_mapping(cls) -> dict:
        polar_coeff_schema = CommaSeparated(Float()) | Str()
        polar_schema = Map({"CL": polar_coeff_schema, "CD": polar_coeff_schema}) | Str()
        return {
            # TODO: this mapping covers all possible segments, but some options are relevant
            #  only for some segments. A better check could be done in second-pass validation.
            Optional("target", default=None): cls._get_target_schema(),
            Optional("engine_setting", default=None): Str(),
            Optional(POLAR_TAG, default=None): polar_schema,
            Optional("thrust_rate", default=None): Float() | Str(),
            Optional("climb_thrust_rate", default=None): Float() | Str(),
            Optional("time_step", default=None): Float(),
            Optional("maximum_flight_level", default=None): Float() | Str(),
            Optional("mass_ratio", default=None): Float() | Str(),
            Optional("reserve_mass_ratio", default=None): Float() | Str(),
            Optional("use_max_lift_drag_ratio", default=None): Bool() | Str(),
        }

    @classmethod
    def _get_segment_mapping(cls, tag=SEGMENT_TAG) -> dict:
        segment_map = {tag: Str()}
        segment_map.update(cls._get_base_step_mapping())
        return segment_map

    @classmethod
    def _get_phase_mapping(cls) -> dict:
        phase_map = {Optional(STEPS_TAG, default=None): Seq(Map(cls._get_segment_mapping()))}
        phase_map.update(cls._get_base_step_mapping())
        return phase_map

    @classmethod
    def _get_phase_in_route_mapping(cls) -> dict:
        phase_map = {PHASE_TAG: Str()}
        phase_map.update(cls._get_base_step_mapping())
        return phase_map

    @classmethod
    def _get_route_mapping(cls) -> dict:
        return {
            "range": cls._get_dimensioned_value_mapping(),
            STEPS_TAG: Seq(Any()),
        }

    @classmethod
    def _get_dimensioned_value_mapping(cls):
        return (
            Float() | Str() | Map({"value": Float() | Str(), Optional("unit", default=None): Str()})
        )

    @classmethod
    def _get_mission_mapping(cls) -> dict:
        return {
            "name": Str(),
            STEPS_TAG: Seq(
                Map(
                    {
                        Optional(ROUTE_TAG, default=None): Str(),
                        Optional(PHASE_TAG, default=None): Str(),
                    }
                )
            ),
        }


class SegmentNames(Enum):
    """
    Class that lists available flight segments.

    Enum values are linked to matching implementation with :meth:`get_segment_class`.
    """

    ALTITUDE_CHANGE = "altitude_change"
    TRANSITION = "transition"
    CRUISE = "cruise"
    OPTIMAL_CRUISE = "optimal_cruise"
    BREGUET = "breguet"
    SPEED_CHANGE = "speed_change"
    HOLDING = "holding"
    TAXI = "taxi"

    @classmethod
    def string_values(cls) -> Set[str]:
        """

        :return: the list of available segments as strings
        """
        return {step.value for step in cls}

    @classmethod
    def get_segment_class(cls, value: Union["SegmentNames", str]) -> type:
        """

        :param value: a SegmentNames instance or a string among possible values of SegmentNames
        :return: the matching implementation class
        """
        segments = {
            cls.ALTITUDE_CHANGE.value: AltitudeChangeSegment,
            cls.TRANSITION.value: DummyTransitionSegment,
            cls.CRUISE.value: ClimbAndCruiseSegment,
            cls.OPTIMAL_CRUISE.value: OptimalCruiseSegment,
            cls.BREGUET.value: BreguetCruiseSegment,
            cls.SPEED_CHANGE.value: SpeedChangeSegment,
            cls.HOLDING.value: HoldSegment,
            cls.TAXI.value: TaxiSegment,
        }
        return segments[value]
