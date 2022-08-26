"""
Schema for mission definition files.
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

import json
from collections import OrderedDict
from importlib.resources import open_text
from os import PathLike
from typing import Union

from ensure import Ensure
from jsonschema import validate
from ruamel.yaml import YAML

from . import resources

JSON_SCHEMA_NAME = "mission_schema.json"

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


class MissionDefinition(OrderedDict):
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
        yaml = YAML(typ="safe", pure=True)

        with open(file_path) as yaml_file:
            data = yaml.load(yaml_file)

        with open_text(resources, JSON_SCHEMA_NAME) as json_file:
            json_schema = json.loads(json_file.read())
        validate(data, json_schema)

        self._validate(data)
        self.update(data)

    @classmethod
    def _validate(cls, content: dict):
        """
        Does a second pass validation of file content.

        Also applies thess features:
            * None values are set back to "~".
            *       - polar: foo:bar
                is translated to:
                    - polar:
                        CL: foo:bar:CL
                        CD: foo:bar:CD

        Errors are raised if file content is incorrect.

        :param content:
        """
        phase_names = set(content[PHASE_DEFINITIONS_TAG].keys())

        for route_definition in content[ROUTE_DEFINITIONS_TAG].values():
            for part in list(route_definition[CLIMB_PARTS_TAG]) + list(
                route_definition[DESCENT_PARTS_TAG]
            ):
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

        cls._convert_none_values(content)

    @classmethod
    def _convert_none_values(cls, struct: Union[dict, list]):
        """
        Recursively transforms any None value in struct to "~"
        """
        if isinstance(struct, dict):
            for key, value in struct.items():
                if value is None:
                    struct[key] = "~"
                else:
                    cls._convert_none_values(value)
        elif isinstance(struct, list):
            for item in struct:
                cls._convert_none_values(item)
