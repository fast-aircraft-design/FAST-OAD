"""
Schema for mission definition files.
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
    YAML,
    CommaSeparated,
    ScalarValidator,
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
RESERVE_TAG = "reserve"
PARTS_TAG = "parts"
CLIMB_PARTS_TAG = "climb_parts"
CRUISE_PART_TAG = "cruise_part"
DESCENT_PARTS_TAG = "descent_parts"
MISSION_DEFINITION_TAG = "missions"
ROUTE_DEFINITIONS_TAG = "routes"
PHASE_DEFINITIONS_TAG = "phases"
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
        phase_names = set(content[PHASE_DEFINITIONS_TAG].keys())

        for phase_definition in content[PHASE_DEFINITIONS_TAG].values():
            cls._process_polar_definition(phase_definition)
            for segment_definition in phase_definition[PARTS_TAG]:
                cls._process_polar_definition(segment_definition)

        for route_definition in content[ROUTE_DEFINITIONS_TAG].values():
            cls._process_polar_definition(route_definition[CRUISE_PART_TAG])
            for part in list(route_definition[CLIMB_PARTS_TAG]) + list(
                route_definition[DESCENT_PARTS_TAG]
            ):
                cls._process_polar_definition(part)
                Ensure(part[PHASE_TAG]).is_in(phase_names)

        for mission_definition in content[MISSION_DEFINITION_TAG].values():
            reserve_count = 0
            for part in mission_definition[PARTS_TAG]:
                part_type, value = tuple(*part.items())
                if part_type == PHASE_TAG:
                    Ensure(value).is_in(content[PHASE_DEFINITIONS_TAG].keys())
                elif part_type == ROUTE_TAG:
                    Ensure(value).is_in(content[ROUTE_DEFINITIONS_TAG].keys())
                elif part_type == RESERVE_TAG:
                    reserve_count += 1
                    Ensure(value["ref"]).is_in(content[ROUTE_DEFINITIONS_TAG].keys())
            Ensure(reserve_count).is_less_than_or_equal_to(1)
            if reserve_count == 1:
                # reserve definition should be the last part
                Ensure(part_type).equals(RESERVE_TAG)

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
                MISSION_DEFINITION_TAG: MapPattern(Str(), Map(cls._get_mission_mapping())),
            }
        )

    @classmethod
    def _get_target_schema(cls) -> Map:
        target_schema_map = {}
        for key in [f.name for f in fields(FlightPoint)]:
            target_schema_map[Optional(key, default=None)] = cls._get_value_mapping()
        return Map(target_schema_map)

    @classmethod
    def _get_base_part_mapping(cls) -> dict:
        polar_coeff_schema = CommaSeparated(Float()) | Str()
        polar_schema = Map({"CL": polar_coeff_schema, "CD": polar_coeff_schema}) | Str()
        return {
            # TODO: this mapping covers all possible segments, but some options are relevant
            #  only for some segments. A better check could be done in second-pass validation.
            Optional("target", default=None): cls._get_target_schema(),
            Optional("engine_setting", default=None): cls._get_value_mapping(Str(), False),
            Optional(POLAR_TAG, default=None): polar_schema,
            Optional("thrust_rate", default=None): cls._get_value_mapping(has_unit=False),
            Optional("climb_thrust_rate", default=None): cls._get_value_mapping(has_unit=False),
            Optional("time_step", default=None): cls._get_value_mapping(),
            Optional("maximum_flight_level", default=None): cls._get_value_mapping(has_unit=False),
            Optional("mass_ratio", default=None): cls._get_value_mapping(has_unit=False),
            Optional("reserve_mass_ratio", default=None): cls._get_value_mapping(has_unit=False),
            Optional("use_max_lift_drag_ratio", default=None): cls._get_value_mapping(
                Bool(), False
            ),
        }

    @classmethod
    def _get_segment_mapping(cls, tag=SEGMENT_TAG) -> dict:
        segment_map = {tag: Str()}
        segment_map.update(cls._get_base_part_mapping())
        return segment_map

    @classmethod
    def _get_phase_mapping(cls) -> dict:
        phase_map = {Optional(PARTS_TAG, default=None): Seq(Map(cls._get_segment_mapping()))}
        phase_map.update(cls._get_base_part_mapping())
        return phase_map

    @classmethod
    def _get_phase_in_route_mapping(cls) -> dict:
        phase_map = {PHASE_TAG: Str()}
        phase_map.update(cls._get_base_part_mapping())
        return phase_map

    @classmethod
    def _get_route_mapping(cls) -> dict:
        return {
            Optional("range", default=None): cls._get_value_mapping(),
            Optional(CLIMB_PARTS_TAG, default=None): Seq(Map(cls._get_phase_in_route_mapping())),
            CRUISE_PART_TAG: Map(cls._get_segment_mapping()),
            Optional(DESCENT_PARTS_TAG, default=None): Seq(Map(cls._get_phase_in_route_mapping())),
        }

    @classmethod
    def _get_value_mapping(cls, value_type: ScalarValidator = Float(), has_unit=True):
        map_dict = {"value": Float() | Str()}
        if has_unit:
            map_dict[Optional("unit", default=None)] = Str()

        return value_type | Str() | Map(map_dict)

    @classmethod
    def _get_mission_mapping(cls) -> dict:
        return {
            PARTS_TAG: Seq(
                Map(
                    {
                        Optional(ROUTE_TAG, default=None): Str(),
                        Optional(PHASE_TAG, default=None): Str(),
                        Optional(RESERVE_TAG, default=None): Map(
                            {"ref": Str(), "multiplier": Float() | Str()}
                        ),
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
        return {part.value for part in cls}

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
