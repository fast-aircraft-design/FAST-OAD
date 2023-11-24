"""Base classes for mission computation."""
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
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import BaseDataClass
from .exceptions import FastUnknownMissionElementError


@dataclass
class IFlightPart(ABC, BaseDataClass):
    """
    Base class for all flight parts.
    """

    name: str = ""
    target: FlightPoint = field(init=False, default_factory=FlightPoint)

    @abstractmethod
    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        """
        Computes a flight sequence from provided start point.

        :param start: the initial flight point, defined for `altitude`, `mass` and speed
                      (`true_airspeed`, `equivalent_airspeed` or `mach`). Can also be
                      defined for `time` and/or `ground_distance`.
        :return: a pandas DataFrame where column names match fields of
                 :class:`~fastoad.model_base.flight_point.FlightPoint`
        """


@dataclass
class FlightSequence(IFlightPart):
    """
    Defines and computes a flight sequence.

    Use .extend() method to add a list of parts in the sequence.
    """

    #: Consumed mass between sequence start and target mass, if any defined
    consumed_mass_before_input_weight: float = field(default=0.0, init=False)

    #: List of flight points for each part of the sequence, obtained after
    #  running :meth:`compute_from`
    part_flight_points: List[pd.DataFrame] = field(default_factory=list, init=False)

    _sequence: List[IFlightPart] = field(default_factory=list, init=False)

    _target: FlightPoint = None

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        if self._target is not None:
            self._sequence[-1].target = self._target

        self.part_flight_points = []
        part_start = deepcopy(start)
        part_start.scalarize()

        self.consumed_mass_before_input_weight = 0.0
        for part in self._sequence:
            # This check has to be done first because relative target parameters
            # will be made absolute during compute_from()
            part_has_target_mass = not (part.target.mass is None or part.target.is_relative("mass"))

            flight_points = part.compute_from(part_start)

            if isinstance(part, FlightSequence):
                self.consumed_mass_before_input_weight += part.consumed_mass_before_input_weight

            # If a part has a target mass, computed mass of all previous part must be
            # offset so this target will be reached.
            # (mass consumption of previous parts is assumed independent of aircraft mass)
            if part_has_target_mass:
                mass_offset = flight_points.iloc[0].mass - part_start.mass
                for previous_flight_points in self.part_flight_points:
                    previous_flight_points.mass += mass_offset
                self.consumed_mass_before_input_weight = flight_points.iloc[-1].consumed_fuel

            if len(self.part_flight_points) > 0 and len(flight_points) > 1:
                # First point of the segment is omitted, as it is the last of previous segment.
                #
                # But sometimes (especially in the case of simplistic segments), the new first
                # point may contain more information than the previous last one. In such case,
                # it is interesting to complete the previous last one.
                last_flight_points = self.part_flight_points[-1]
                last_index = last_flight_points.index[-1]
                for name in flight_points.columns:
                    value = last_flight_points.loc[last_index, name]
                    if not value:
                        last_flight_points.loc[last_index, name] = flight_points.loc[0, name]

                self.part_flight_points.append(flight_points.iloc[1:])

            else:
                # But it is kept if the computed segment is the first one.
                self.part_flight_points.append(flight_points)

            part_start = FlightPoint.create(flight_points.iloc[-1])
            part_start.scalarize()

        if self.part_flight_points:
            return pd.concat(self.part_flight_points).reset_index(drop=True)

    @property
    def target(self) -> Optional[FlightPoint]:
        """Target of the last element of current sequence."""
        if hasattr(self, "_sequence") and len(self._sequence) > 0:
            return self._sequence[-1].target

        return None

    @target.setter
    def target(self, value: FlightPoint):
        if hasattr(self, "_sequence") and len(self._sequence) > 0:
            self._sequence[-1].target = value
        else:
            self._target = value

    def append(self, flight_part: IFlightPart):
        """Append flight part to the end of the sequence."""
        self._sequence.append(flight_part)

    def clear(self):
        """Remove all parts from flight sequence."""
        self._sequence.clear()
        self.part_flight_points.clear()
        self.consumed_mass_before_input_weight = 0.0

    def extend(self, seq):
        """Extend flight sequence by appending elements from the iterable."""
        self._sequence.extend(seq)

    def index(self, *args, **kwargs):
        """Return first index of value (see list.index())."""
        return self._sequence.index(*args, **kwargs)

    def __len__(self):
        return len(self._sequence)

    def __getitem__(self, item):
        return self._sequence[item]

    def __add__(self, other):
        result = self.__class__()
        result.extend(other)
        return result

    def __iter__(self):
        return iter(self._sequence)


class RegisterElement:
    """
    Base class for decorators that can associate a class with a keyword.

    When subclassing, the argument 'base_class' allow to specify a class that should be
    a parent of all registered classes. A specific check will be done at register time.

        >>> class RegisterFeature(RegisterElement, base_class=AbstractFeature)
        >>>   ...

    Then the newly created class may be used as decorator like:

        >>> @RegisterFeature("identifier_foo")
        >>> class FooFeature(AbstractFeature):
        >>>     ...

    Then the registered class can be obtained by:

        >>> my_class = RegisterFeature.get_class("identifier_foo")
    """

    _base_class = object
    _keyword_vs_implementation: Dict[str, type] = {}

    @classmethod
    def __init_subclass__(cls, *, base_class=object):
        cls._base_class = base_class

    def __init__(self, keyword=""):
        self._keyword = keyword

    def __call__(self, class_to_register):
        cls = type(self)
        cls._add_element(self._keyword, class_to_register)
        return class_to_register

    @classmethod
    def _add_element(cls, keyword: str, element_class: type):
        """
        Adds an element definition.

        :param keyword: element name (mission file keyword)
        :param element_class: element implementation
        """
        if issubclass(element_class, cls._base_class):
            cls._keyword_vs_implementation[keyword] = element_class
        else:
            raise RuntimeWarning(
                f'"{element_class}" is not registered because it'
                f"does not derive from {cls._base_class}."
            )

    @classmethod
    def get_class(cls, keyword) -> Optional[type]:
        """
        Provides the element implementation for provided name.

        :param keyword:
        :return: the element implementation
        :raise FastUnknownMissionElementError: if element has not been declared.
        """
        element_class = cls._keyword_vs_implementation.get(keyword)

        if element_class is None:
            raise FastUnknownMissionElementError(keyword)

        return element_class

    @classmethod
    def get_classes(cls) -> Dict[str, type]:
        """

        :return: dict that associates keywords to their registered class.
        """
        return cls._keyword_vs_implementation.copy()
