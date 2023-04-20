"""
Classes for managing internal structures of missions.

The mission file provides a "human" definition of the mission.
Structures are the translation of this human definition, that is ready to
be transformed into a Python implementation.
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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
    POLAR_TAG,
    ROUTE_DEFINITIONS_TAG,
    ROUTE_TAG,
    SEGMENT_TAG,
)
from ...segments.base import RegisterSegment


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
    variable_prefix: str = ""

    _structure: dict = field(default=None, init=False)

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
        if self.__class__.type:
            self._structure[TYPE_TAG] = self.__class__.type
        self._structure[NAME_TAG] = self.qualified_name
        self._process_polar(self._structure)
        self._parse_inputs(self._structure, self._input_definitions)

    @property
    def structure(self) -> dict:
        """A dictionary that is ready to be translated to the matching implementation."""
        for builder, placeholder in self._builders:
            placeholder.update(builder.structure)
            self._input_definitions += builder.get_input_definitions()
        self._builders = []  # Builders have been used and can be forgotten.
        return self._structure

    def get_input_definitions(self) -> List[InputDefinition]:
        """List of InputDefinition instances in the structure."""
        return self._input_definitions + list(
            chain(*[builder.get_input_definitions() for builder, _ in self._builders])
        )

    def process_builder(self, builder: "AbstractStructureBuilder") -> dict:
        """
        Method to be used when another StructureBuilder object should be inserted in
        :attr:`structure`.

        Not using this method will prevent a correct processing of :attr:`input_definitions`.

        .. note::

            The returned object is always an empty dict. It is actually a memory reference that
            will allow to fill this "placeholder" later with the final result of the builder, that
            cannot be completely known when builder is created from read definition.

        :param builder: the builder object
        :return: the object that has to be put at location where the builder result should be used
        """

        placeholder = {}
        self._builders.append((builder, placeholder))
        return placeholder

    @abstractmethod
    def _build(self, definition: dict) -> dict:
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

    def _parse_inputs(
        self,
        structure,
        input_definitions: List[InputDefinition],
        parent=None,
        part_identifier="",
        segment_class=None,
    ):
        """
        Returns the `definition` structure where all inputs (string/numeric values, numeric lists,
        dicts with a "value key"), have been converted to an InputDefinition instance.

        Created InputDefinition instances are stored in provided input_definitions.

        :param structure:
        :param parent:
        :param part_identifier:
        :return: amended definition
        """

        if isinstance(structure, dict):
            if "value" in structure:
                input_definition = InputDefinition.from_dict(
                    parent, structure, part_identifier=part_identifier, prefix=self.variable_prefix
                )
                input_definitions.append(input_definition)
                return input_definition

            part_identifier = structure.get(NAME_TAG, part_identifier)
            if SEGMENT_TYPE_TAG in structure:
                segment_class = RegisterSegment.get_class(structure[SEGMENT_TYPE_TAG])
            else:
                segment_class = None
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
                if (
                    segment_class
                    and isinstance(value, dict)
                    and isinstance(value.get("value"), str)
                    and self._is_shape_by_conn(key, segment_class)
                ):
                    value["shape_by_conn"] = True

                structure[key] = self._parse_inputs(
                    value,
                    input_definitions,
                    parent=key,
                    part_identifier=part_identifier,
                    segment_class=segment_class,
                )
            return structure

        # Here structure is not a dict, hence a directly given value.
        key, value = parent, structure
        if key == POLAR_TAG:
            return None
        input_definition = InputDefinition(
            key, value, part_identifier=part_identifier, prefix=self.variable_prefix
        )
        if segment_class and isinstance(value, str):
            input_definition.shape_by_conn = self._is_shape_by_conn(key, segment_class)
        input_definitions.append(input_definition)
        return input_definition

    @staticmethod
    def _is_shape_by_conn(key, segment_class) -> bool:
        """
        Here variables that are expected to be arrays or lists in the provided segment class are
        attributed the "shape_by_conn=True" property.
        """
        segment_fields = [fld for fld in fields(segment_class) if fld.name == key]
        return len(segment_fields) == 1 and issubclass(segment_fields[0].type, (list, np.ndarray))

    def _process_polar(self, structure):
        """
        Polar data are handled specifically, as it is a particular parameter of segments (
        a Polar class).

        If "foo:bar:baz" is provided as `polar_structure`, it is replaced by the dict
        { "CL": {value:"foo:bar:baz:CL", "shape_by_conn": True},
          "CD": {value:"foo:bar:baz:CD", "shape_by_conn": True}}

        Also, even if `polar_structure` is a dict, it is ensured that it has the structure above.
        """

        if POLAR_TAG in structure:
            builder = PolarStructureBuilder(
                structure[POLAR_TAG], "", self.qualified_name, self.variable_prefix
            )
            structure[POLAR_TAG] = self.process_builder(builder)


class DefaultStructureBuilder(AbstractStructureBuilder):
    """
    Builder for structures that do not need to process the given definition.

    :param definition: the definition for the part only
    """

    def _build(self, definition: dict) -> dict:
        return deepcopy(definition)


class PolarStructureBuilder(AbstractStructureBuilder, structure_type=POLAR_TAG):
    """
    Structure builder for polar definition.

    :param definition: the definition for the polar only
    """

    def _build(self, definition: dict) -> dict:
        polar_structure = {}
        if isinstance(definition, str):
            polar_structure = {
                "CL": {"value": definition + ":CL", "shape_by_conn": True},
                "CD": {"value": definition + ":CD", "shape_by_conn": True},
            }

        elif isinstance(definition, dict):
            polar_structure = deepcopy(definition)
            for key in ["CL", "CD", "alpha"]:
                if key in polar_structure:
                    if isinstance(polar_structure[key], str):
                        polar_structure[key] = {
                            "value": polar_structure[key],
                            "shape_by_conn": True,
                        }
                    elif isinstance(polar_structure[key], dict):
                        polar_structure[key]["shape_by_conn"] = True

        return polar_structure


class SegmentStructureBuilder(AbstractStructureBuilder, structure_type=SEGMENT_TAG):
    """
    Structure builder for segment definition.

    :param definition: the definition for the segment only
    """

    def _build(self, definition: dict) -> dict:
        segment_structure = deepcopy(definition)
        del segment_structure[SEGMENT_TAG]
        segment_structure[SEGMENT_TYPE_TAG] = definition[SEGMENT_TAG]

        return segment_structure


class PhaseStructureBuilder(AbstractStructureBuilder, structure_type=PHASE_TAG):
    """
    Structure builder for phase definition.

    :param definition: the whole content of definition file
    """

    def _build(self, definition: dict) -> dict:
        phase_definition = definition[PHASE_DEFINITIONS_TAG][self.name]
        phase_structure = deepcopy(phase_definition)

        for i, part in enumerate(phase_definition[PARTS_TAG]):
            if PHASE_TAG in part:
                builder = PhaseStructureBuilder(
                    definition, part[PHASE_TAG], self.qualified_name, self.variable_prefix
                )
            elif SEGMENT_TAG in part:
                builder = SegmentStructureBuilder(
                    part, "", self.qualified_name, self.variable_prefix
                )
            else:
                raise RuntimeError(f"Unexpected structure in definition of phase {self.name}")

            phase_structure[PARTS_TAG][i] = self.process_builder(builder)

        return phase_structure


class RouteStructureBuilder(AbstractStructureBuilder, structure_type=ROUTE_TAG):
    """
    Structure builder for route definition.

    :param definition: the whole content of definition file
    """

    def _build(self, definition: dict) -> dict:
        route_definition = definition[ROUTE_DEFINITIONS_TAG][self.name]
        route_structure = deepcopy(route_definition)

        route_structure[CLIMB_PARTS_TAG] = self._get_route_climb_or_descent_structure(
            definition, route_definition[CLIMB_PARTS_TAG]
        )

        builder = SegmentStructureBuilder(
            route_definition[CRUISE_PART_TAG], "cruise", self.qualified_name, self.variable_prefix
        )
        route_structure[CRUISE_PART_TAG] = self.process_builder(builder)

        route_structure[DESCENT_PARTS_TAG] = self._get_route_climb_or_descent_structure(
            definition, route_definition[DESCENT_PARTS_TAG]
        )

        if POLAR_TAG in route_structure:
            builder = PolarStructureBuilder(
                route_structure[POLAR_TAG], "", self.qualified_name, self.variable_prefix
            )
            route_structure[POLAR_TAG] = self.process_builder(builder)
        return route_structure

    def _get_route_climb_or_descent_structure(self, global_definition, parts_definition):
        parts = []
        for part_definition in parts_definition:
            phase_name = part_definition["phase"]
            builder = PhaseStructureBuilder(
                global_definition, phase_name, self.qualified_name, self.variable_prefix
            )
            phase_structure = self.process_builder(builder)
            parts.append(phase_structure)
        return parts


class MissionStructureBuilder(AbstractStructureBuilder, structure_type="mission"):
    """
    Structure builder for mission definition.

    :param definition: the whole content of definition file
    """

    def _build(self, definition: dict) -> dict:
        mission_definition = definition[MISSION_DEFINITION_TAG][self.name]
        mission_structure = deepcopy(mission_definition)

        mission_parts = []
        for part_definition in mission_definition[PARTS_TAG]:
            if ROUTE_TAG in part_definition:
                route_name = part_definition[ROUTE_TAG]
                builder = RouteStructureBuilder(
                    definition, route_name, self.qualified_name, self.variable_prefix
                )
            elif PHASE_TAG in part_definition:
                phase_name = part_definition[PHASE_TAG]
                builder = PhaseStructureBuilder(
                    definition, phase_name, self.qualified_name, self.variable_prefix
                )
            elif SEGMENT_TAG in part_definition:
                builder = SegmentStructureBuilder(
                    part_definition, "", self.qualified_name, self.variable_prefix
                )
            else:
                builder = DefaultStructureBuilder(
                    part_definition, "", self.qualified_name, self.variable_prefix
                )

            part_structure = self.process_builder(builder)
            mission_parts.append(part_structure)

        mission_structure[PARTS_TAG] = mission_parts

        return mission_structure

    @property
    def qualified_name(self):
        return self.name
