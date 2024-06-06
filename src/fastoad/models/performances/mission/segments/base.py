"""Base classes for simulating flight segments."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
from typing import Optional, Type

import numpy as np
import pandas as pd
from deprecated import deprecated
from stdatm import AtmosphereSI

from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from ..base import IFlightPart, RegisterElement
from ..exceptions import FastFlightSegmentIncompleteFlightPoint


class RegisterSegment(RegisterElement, base_class=IFlightPart):
    """
    Decorator for registering IFlightPart classes.

        >>> @RegisterSegment("segment_foo")
        >>> class FooSegment(IFlightPart):
        >>>     ...

    Then the registered class can be obtained by:

        >>> my_class = RegisterSegment.get_class("segment_foo")
    """


@deprecated(
    "The way to get registered segments is now to use RegisterSegment.get_class(). "
    "SegmentDefinitions will be removed in FAST-OAD 2.0",
    version="1.5.0",
)
class SegmentDefinitions:
    """
    Class that associates segment names (mission file keywords) and their implementation.
    """

    @classmethod
    def add_segment(cls, segment_name: str, segment_class: Type[IFlightPart]):
        """
        Adds a segment definition.

        :param segment_name: segment names (mission file keyword)
        :param segment_class: segment implementation (derived of :class:`~FlightSegment`)
        """
        RegisterSegment(segment_name)(segment_class)

    @classmethod
    def get_segment_class(cls, segment_name) -> Optional[Type["IFlightPart"]]:
        """
        Provides the segment implementation for provided name.

        :param segment_name:
        :return: the segment implementation (derived of :class:`~FlightSegment`)
        :raise FastUnknownMissionSegmentError: if segment type has not been declared.
        """
        return RegisterSegment.get_class(segment_name)


@deprecated(
    "The way to register segments is now to use decorator RegisterSegment. "
    "RegisteredSegment will be removed in FAST-OAD 2.0",
    version="1.5.0",
)
class RegisteredSegment(IFlightPart, ABC):
    """
    Base class for classes that can be associated with a keyword in mission definition file.

    When subclassing this class, the attribute "mission_file_keyword" can be set,
    so that the segment can be used in mission file definition with this keyword:

        >>> class NewSegment(AbstractFlightSegment, mission_file_keyword="new_segment")
        >>>     ...

    Then in mission definition:

    .. code-block:: yaml

        phases:
            my_phase:
                parts:
                    - segment: new_segment
    """

    @classmethod
    def __init_subclass__(cls, *, mission_file_keyword=""):
        if mission_file_keyword:
            RegisterSegment(mission_file_keyword)(cls)


@dataclass
class AbstractFlightSegment(IFlightPart, ABC):
    """
    Base class for flight path segment.

    As a dataclass, attributes can be set at instantiation.

    .. Important::

        :meth:`compute_from` is the method to call to achieve the segment computation.

        However, when subclassing, the method to overload is :meth:`compute_from_start_to_target`.
        Generic reprocessing of start and target flight points is done in :meth:`compute_from`
        before calling :meth:`compute_from_start_to_target`
    """

    #: A FlightPoint instance that provides parameter values that should all be reached at the
    #: end of :meth:`~fastoad.models.performances.mission.segments.base.FlightSegment.compute_from`.
    #: Possible parameters depend on the current segment. A parameter can also be set to
    #: :attr:`~fastoad.models.performances.mission.segments.base.FlightSegment.CONSTANT_VALUE`
    #: to tell that initial value should be kept during all segment.
    target: FlightPoint = MANDATORY_FIELD

    # the `target` field above will be overloaded by a property, using the hidden value below:
    _target: FlightPoint = field(default=MANDATORY_FIELD, init=False)

    #: The temperature offset for ISA atmosphere model.
    isa_offset: float = 0.0

    #: Using this value will tell to keep the associated parameter constant.
    CONSTANT_VALUE = "constant"  # pylint: disable=invalid-name # used as constant

    # To be noted: this one is not a dataclass field, but an actual class attribute
    _attribute_units = dict(reference_area="m**2", time_step="s")

    @abstractmethod
    def compute_from_start_to_target(self, start, target) -> pd.DataFrame:
        """
        Here should come the implementation for computing flight points
        between start and target flight points.

        :param start:
        :param target: Definition of segment target
        :return: a pandas DataFrame where column names match fields of
                 :class:`~fastoad.model_base.flight_point.FlightPoint`
        """

    @classmethod
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)

        # We want to have self.target as a property to ensure it gets always "scalarized".
        # But properties and dataclasses do not mix very well. It would be possible to
        # declare "target" as property, though it is a dataclass field, but it would then
        # be considered as a field with defined default value (the default being the property
        # object XD ). And since it is followed by fields without default, Python complains.
        #
        # The solution is to define the property afterwards, and since we are in an abstract class,
        # it can be done when subclassing.
        def _get_target(self) -> FlightPoint:
            return self._target

        def _set_target(self, value: FlightPoint):
            value.scalarize()
            # Initializing self._target elsewhere give bad results. Since target is mandatory
            # in constructor, this initialization will happen.
            self._target = value

        cls.target = property(_get_target, _set_target)

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        """
        Computes the flight path segment from provided start point.

        Computation ends when target is attained, or if the computation stops getting
        closer to target.
        For instance, a climb computation with too low thrust will only return one
        flight point, that is the provided start point.

        .. Important::

            When subclasssing, if you need to overload :meth:`compute_from`, you should consider
            overriding :meth:`compute_from_start_to_target` instead. Therefore, you will take
            benefit of the preprocessing of start and target flight points that is done in
            :meth:`compute_from`.


        :param start: the initial flight point, defined for `altitude`, `mass` and speed
                      (`true_airspeed`, `equivalent_airspeed` or `mach`). Can also be
                      defined for `time` and/or `ground_distance`.
        :return: a pandas DataFrame where column names match fields of
                 :class:`~fastoad.model_base.flight_point.FlightPoint`
        """
        # Let's ensure we do not modify the original definitions of start and target
        # during the process
        start_copy = deepcopy(start)

        if start_copy.altitude is not None:
            try:
                self.complete_flight_point(start_copy)
            except FastFlightSegmentIncompleteFlightPoint:
                pass
        start_copy.scalarize()
        start_copy.isa_offset = self.isa_offset

        target_copy = self._target.make_absolute(start_copy)
        target_copy.scalarize()

        if start_copy.time is None:
            start_copy.time = 0.0
        if start_copy.ground_distance is None:
            start_copy.ground_distance = 0.0

        flight_points = self.compute_from_start_to_target(start_copy, target_copy)

        return flight_points

    def complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point.

        Assumes that it is already defined for time, altitude, mass,
        ground distance and speed (TAS, EAS, or Mach).

        :param flight_point: the flight point that will be completed in-place
        """

        self._complete_speed_values(flight_point)

    @staticmethod
    def complete_flight_point_from(flight_point: FlightPoint, source: FlightPoint):
        """
        Sets undefined values in `flight_point` using the ones from `source`.

        The particular case of speeds is taken into account: if at least one speed parameter is
        defined, all other speed parameters are considered defined, because they will be
        deduced when needed.

        :param flight_point:
        :param source:
        """
        speed_fields = {
            "true_airspeed",
            "equivalent_airspeed",
            "calibrated_airspeed",
            "mach",
            "unitary_reynolds",
        }.intersection(flight_point.get_field_names())
        other_fields = list(set(flight_point.get_field_names()) - speed_fields)

        speeds_are_missing = np.all([getattr(flight_point, name) is None for name in speed_fields])

        for field_name in other_fields + speeds_are_missing * list(speed_fields):
            if getattr(flight_point, field_name) is None and not source.is_relative(field_name):
                setattr(flight_point, field_name, getattr(source, field_name))

    @staticmethod
    def consume_fuel(
        flight_point: FlightPoint,
        previous: FlightPoint,
        fuel_consumption: float = None,
        mass_ratio: float = None,
    ):
        """
        This method should be used whenever fuel consumption has to be stored.

        It ensures that "mass" and "consumed_fuel" fields will be kept consistent.

        Mass can be modified using the 'fuel_consumption" argument, or the 'mass_ratio'
        argument. One of them should be provided.

        :param flight_point: the FlightPoint instance where "mass" and "consumed_fuel"
                             fields will get new values
        :param previous: FlightPoint instance that will be the base for the computation
        :param fuel_consumption: consumed fuel, in kg, between 'previous' and 'flight_point'.
                                 Positive when fuel is consumed.
        :param mass_ratio: the ratio flight_point.mass/previous.mass
        """
        flight_point.mass = previous.mass
        flight_point.consumed_fuel = previous.consumed_fuel
        if fuel_consumption is not None:
            flight_point.mass -= fuel_consumption
            flight_point.consumed_fuel += fuel_consumption
        if mass_ratio is not None:
            flight_point.mass *= mass_ratio
            flight_point.consumed_fuel += previous.mass - flight_point.mass

    def _complete_speed_values(
        self, flight_point: FlightPoint, raise_error_on_missing_speeds=True
    ) -> bool:
        """
        Computes consistent values between TAS, EAS and Mach, assuming one of them is defined.
        """
        atm = self._get_atmosphere_point(flight_point.altitude)

        if flight_point.true_airspeed is None:
            if flight_point.mach is not None:
                atm.mach = flight_point.mach
            elif flight_point.equivalent_airspeed is not None:
                atm.equivalent_airspeed = flight_point.equivalent_airspeed
            elif raise_error_on_missing_speeds:
                raise FastFlightSegmentIncompleteFlightPoint(
                    "Flight point should be defined for true_airspeed, "
                    "equivalent_airspeed, or mach."
                )
            else:
                return False
            flight_point.true_airspeed = atm.true_airspeed
        else:
            atm.true_airspeed = flight_point.true_airspeed

        flight_point.mach = atm.mach
        flight_point.equivalent_airspeed = atm.equivalent_airspeed
        return True

    def _get_atmosphere_point(self, altitude: float) -> AtmosphereSI:
        """
        Convenience method to ensure used atmosphere model is initiated with :attr:`delta_isa`.

        :param altitude: in meters
        :return: AtmosphereSI instantiated from provided altitude and :attr:`delta_isa`
        """
        return AtmosphereSI(altitude, self.isa_offset)
