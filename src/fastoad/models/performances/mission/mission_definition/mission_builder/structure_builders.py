"""
Classes for managing internal structures of missions.

The mission file provides a "human" definition of the mission.
Structures are the translation of this human definition, that is ready to
be transformed in a Python implementation.
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
from collections import OrderedDict
from copy import deepcopy
from dataclasses import InitVar, dataclass, field, fields
from itertools import chain
from typing import List, Tuple

import numpy as np

from .constants import NAME_TAG, SEGMENT_TYPE_TAG, TYPE_TAG
from .input_definition import InputDefinition
from ..schema import (
    CLIMB_PARTS_TAG,
    CRUISE_PART_TAG,
    DESCENT_PARTS_TAG,
    MISSION_DEFINITION_TAG,
    PARTS_TAG,
    PHASE_DEFINITIONS_TAG,
    PHASE_TAG,
    ROUTE_DEFINITIONS_TAG,
    ROUTE_TAG,
    SEGMENT_TAG,
)
from ...segments.base import SegmentDefinitions


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

    @property
    def qualified_name(self):
        """Name of the current structure, preceded by the parent names, separated by colons (:)."""
        if not self.parent_name:
            return self.name

        name = self.parent_name
        if self.name:
            name += f":{self.name}"
        return name

    def _parse_inputs(self, structure, input_definitions, parent=None, part_identifier=""):
        """
        Returns the `definition` structure where all inputs (string/numeric values, numeric lists,
        dicts with a "value key"), have been converted to an InputDefinition instance.

        Created InputDefinition instances are stored in self._input_definitions.

        :param structure:
        :param parent:
        :param part_identifier:
        :return: amended definition
        """

        if isinstance(structure, dict):
            if "polar" in structure:
                structure["polar"] = self._process_polar(structure["polar"])

            if "value" in structure:
                input_definition = InputDefinition.from_dict(
                    parent, structure, part_identifier=part_identifier
                )
                input_definitions.append(input_definition)
                return input_definition

            part_identifier = structure.get(NAME_TAG, part_identifier)
            segment_class = SegmentDefinitions.get_segment_class(structure.get(SEGMENT_TYPE_TAG))
            for key, value in structure.items():
                if key in [
                    NAME_TAG,
                    TYPE_TAG,
                    SEGMENT_TYPE_TAG,
                    PARTS_TAG,
                    CLIMB_PARTS_TAG,
                    DESCENT_PARTS_TAG,
                    CRUISE_PART_TAG,
                ]:
                    continue
                if segment_class:
                    self._process_shape_by_conn(key, value, segment_class)

                structure[key] = self._parse_inputs(
                    value,
                    input_definitions,
                    parent=key,
                    part_identifier=part_identifier,
                )
            return structure

        input_definition = InputDefinition(parent, structure, part_identifier=part_identifier)
        input_definitions.append(input_definition)
        return input_definition

    @staticmethod
    def _process_shape_by_conn(key, value, segment_class):
        """
        Here variables that are expected to be arrays or lists in the provided segment class are
        attributed the "shape_by_conn=True" property.
        """
        segment_fields = [fld for fld in fields(segment_class) if fld.name == key]
        if len(segment_fields) == 1 and isinstance(value, dict) and "value" in value:
            value["shape_by_conn"] = segment_fields[0].type in [list, np.ndarray]

    @staticmethod
    def _process_polar(polar_structure):
        """
        Polar data are handled specifically, as it a particular parameter of segments (
        a Polar class).

        If "foo:bar:baz" is provided as `polar_structure`, it is replaced by the dict
        { "CL": {value:"foo:bar:baz:CL", "shape_by_conn": True},
          "CD": {value:"foo:bar:baz:CD", "shape_by_conn": True}}

        Also, even if `polar_structure` is a dict, it is ensured that it has the structure above.
        """

        if isinstance(polar_structure, str):
            polar_structure = OrderedDict(
                {
                    "CL": {"value": polar_structure + ":CL", "shape_by_conn": True},
                    "CD": {"value": polar_structure + ":CD", "shape_by_conn": True},
                }
            )
        elif isinstance(polar_structure, dict):
            for key in ["CL", "CD"]:
                if isinstance(polar_structure[key], str):
                    polar_structure[key] = {"value": polar_structure[key], "shape_by_conn": True}
                elif isinstance(polar_structure[key], dict):
                    polar_structure[key]["shape_by_conn"] = True

        return polar_structure


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
