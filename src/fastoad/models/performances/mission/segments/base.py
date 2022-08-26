"""Base classes for simulating flight segments."""
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

import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Type

import numpy as np
import pandas as pd
from aenum import Enum, extend_enum
from deprecated import deprecated
from scipy.constants import g
from scipy.optimize import root_scalar
from stdatm import AtmosphereSI

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from fastoad.model_base.propulsion import IPropulsion
from fastoad.models.performances.mission.polar import Polar
from ..base import IFlightPart
from ..exceptions import FastFlightSegmentIncompleteFlightPoint

_LOGGER = logging.getLogger(__name__)  # Logger for this module

DEFAULT_TIME_STEP = 0.2


class SegmentDefinitions(Enum):
    """
    Class that associates segment names (mission file keywords) and their implementation.
    """

    @classmethod
    def add_segment(cls, segment_name: str, segment_class: Type["AbstractFlightSegment"]):
        """
        Adds a segment definition.

        :param segment_name: segment names (mission file keyword)
        :param segment_class: segment implementation (derived of :class:`~FlightSegment`)
        """
        if issubclass(segment_class, AbstractFlightSegment):
            extend_enum(cls, segment_name, segment_class)
        else:
            raise RuntimeWarning(
                f'"{segment_name}" is ignored as segment name because its associated class '
                "does not derive from FlightSegment."
            )

    @classmethod
    def get_segment_class(cls, segment_name) -> Optional[Type["AbstractFlightSegment"]]:
        """
        Provides the segment implementation for provided name.

        :param segment_name:
        :return: the segment implementation (derived of :class:`~FlightSegment`),
                 or None if segment_name is not known
        """
        try:
            enum = cls[segment_name]
        except KeyError:
            enum = None

        return enum.value if enum else None


@dataclass
class AbstractFlightSegment(IFlightPart, ABC):
    """
    Base class for flight path segment.

    As a dataclass, attributes can be set at instantiation.

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
    def __init_subclass__(cls, *, mission_file_keyword="", attribute_units: Dict[str, str] = None):
        if mission_file_keyword:
            SegmentDefinitions.add_segment(mission_file_keyword, cls)
        cls._attribute_units = cls._attribute_units.copy()
        if attribute_units:
            cls._attribute_units.update(attribute_units)

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

    @classmethod
    def get_attribute_unit(cls, attribute_name: str) -> str:
        """Returns unit for specified attribute."""
        return cls._attribute_units.get(attribute_name)

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        """
        Computes the flight path segment from provided start point.

        Computation ends when target is attained, or if the computation stops getting
        closer to target.
        For instance, a climb computation with too low thrust will only return one
        flight point, that is the provided start point.

        .. Important::

            When subclasssing, if you need to overload :meth:`compute_from`, you should consider
            overriding :meth:`_compute_from` instead. Therefore, you will take benefit of the
            preprocessing of start and target flight points that is done in :meth:`compute_from`


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


@dataclass
class AbstractTimeStepFlightSegment(
    AbstractFlightSegment,
    ABC,
):
    """
    Base class for time step computation flight segments.

    This class implements the time computation. For this computation to work, subclasses must
    implement abstract methods :meth:`get_distance_to_target`,
    :meth:`get_gamma_and_acceleration` and :meth:`compute_propulsion`.
    """

    #: A IPropulsion instance that will be called at each time step.
    propulsion: IPropulsion = MANDATORY_FIELD

    #: The Polar instance that will provide drag data.
    polar: Polar = MANDATORY_FIELD

    #: The reference area, in m**2.
    reference_area: float = MANDATORY_FIELD

    #: Used time step for computation (actual time step can be lower at some particular times of
    #: the flight path).
    time_step: float = DEFAULT_TIME_STEP

    #: Minimum and maximum authorized altitude values. If computed altitude gets beyond these
    #: limits, computation will be interrupted and a warning message will be issued in logger.
    altitude_bounds: tuple = (-500.0, 40000.0)

    #: Minimum and maximum authorized mach values. If computed Mach gets beyond these limits,
    #: computation will be interrupted and a warning message will be issued in logger.
    mach_bounds: tuple = (0.0, 5.0)

    #: If True, computation will be interrupted if a parameter stops getting closer to target
    #: between two iterations (which can mean the provided thrust rate is not adapted).
    interrupt_if_getting_further_from_target: bool = True

    #: The EngineSetting value associated to the segment. Can be used in the
    #: propulsion model.
    engine_setting: EngineSetting = EngineSetting.CLIMB

    @abstractmethod
    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:
        """
        Computes a "distance" from last flight point to target.

        Computed does not need to have a real meaning.
        The important point is that it must be signed so that algorithm knows on
        which "side" of the target we are.
        And of course, it should be 0. if flight point is on target.

        :param flight_points: list of all currently computed flight_points
        :param target: segment target (will not contain relative values)
        :return: O. if target is attained, a non-null value otherwise
        """

    @abstractmethod
    def compute_propulsion(self, flight_point: FlightPoint):
        """
        Computes propulsion data.

        Provided flight point is modified in place.

        Generally, this method should end with::

            self.propulsion.compute_flight_points(flight_point)

        :param flight_point:
        """

    @abstractmethod
    def get_gamma_and_acceleration(self, flight_point: FlightPoint) -> Tuple[float, float]:
        """
        Computes slope angle (gamma) and acceleration.

        :param flight_point: parameters after propulsion model has been called
                             (i.e. mass, thrust and drag are available)
        :return: slope angle in radians and acceleration in m**2/s
        """

    def complete_flight_point(self, flight_point: FlightPoint):
        super().complete_flight_point(flight_point)
        if flight_point.altitude is not None:
            atm = self._get_atmosphere_point(flight_point.altitude)
            reference_force = (
                0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_area
            )

            if self.polar:
                flight_point.CL = flight_point.mass * g / reference_force
                flight_point.CD = self.polar.cd(flight_point.CL)
            else:
                flight_point.CL = flight_point.CD = 0.0
            flight_point.drag = flight_point.CD * reference_force
        flight_point.engine_setting = self.engine_setting
        self.compute_propulsion(flight_point)
        flight_point.slope_angle, flight_point.acceleration = self.get_gamma_and_acceleration(
            flight_point
        )

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        flight_points = [start]
        previous_point_to_target = self.get_distance_to_target(flight_points, target)
        tol = 1.0e-5  # Such accuracy is not needed, but ensures reproducibility of results.
        while np.abs(previous_point_to_target) > tol:
            self._add_new_flight_point(flight_points, self.time_step)
            last_point_to_target = self.get_distance_to_target(flight_points, target)

            if last_point_to_target * previous_point_to_target < 0.0:

                # Target has been exceeded. Let's look for the exact time step using root_scalar.
                def replace_last_point(time_step):
                    """
                    Replaces last point of flight_points.

                    :param time_step: time step for new point
                    :return: new distance to target
                    """

                    if isinstance(time_step, np.ndarray):
                        # root_scalar() will provide time_step ad (1,) array, resulting
                        # in all parameters of the new flight point being also (1,) arrays.
                        # We want to avoid that
                        time_step = time_step.item()
                    del flight_points[-1]
                    self._add_new_flight_point(flight_points, time_step)
                    return self.get_distance_to_target(flight_points, target)

                root_scalar(
                    replace_last_point, x0=self.time_step, x1=self.time_step / 2.0, rtol=tol
                )
                last_point_to_target = self.get_distance_to_target(flight_points, target)
            elif (
                np.abs(last_point_to_target) > np.abs(previous_point_to_target)
                # If self.target.CL is defined, it means that we look for an optimal altitude and
                # that target altitude can move, so it would be normal to get further from target.
                and self.interrupt_if_getting_further_from_target
            ):
                # We get further from target. Let's stop without this point.
                _LOGGER.warning(
                    'Target cannot be reached in "%s". Segment computation interrupted.'
                    "Please review the segment settings, especially thrust_rate.",
                    self.name,
                )
                del flight_points[-1]
                break

            msg = self._check_values(flight_points[-1])
            if msg:
                _LOGGER.warning(msg + ' Segment computation interrupted in "%s".', self.name)
                break

            previous_point_to_target = last_point_to_target

        flight_points_df = pd.DataFrame(flight_points)
        return flight_points_df

    def compute_next_flight_point(
        self, flight_points: List[FlightPoint], time_step: float
    ) -> FlightPoint:
        """
        Computes time, altitude, speed, mass and ground distance of next flight point.

        :param flight_points: previous flight points
        :param time_step: time step for computing next point
        :return: the computed next flight point
        """
        start = flight_points[0]
        previous = flight_points[-1]
        next_point = FlightPoint()

        next_point.mass = previous.mass - self.propulsion.get_consumed_mass(previous, time_step)
        next_point.time = previous.time + time_step
        next_point.ground_distance = (
            previous.ground_distance
            + previous.true_airspeed * time_step * np.cos(previous.slope_angle)
        )
        self._compute_next_altitude(next_point, previous)

        if self.target.true_airspeed == self.CONSTANT_VALUE:
            next_point.true_airspeed = previous.true_airspeed
        elif self.target.equivalent_airspeed == self.CONSTANT_VALUE:
            next_point.equivalent_airspeed = start.equivalent_airspeed
        elif self.target.mach == self.CONSTANT_VALUE:
            next_point.mach = start.mach
        else:
            next_point.true_airspeed = previous.true_airspeed + time_step * previous.acceleration

        # The naming is not done in complete_flight_point for not naming the start point
        next_point.name = self.name
        return next_point

    def _check_values(self, flight_point: FlightPoint) -> str:
        """
        Checks that computed values are consistent.

        May be overloaded for doing specific additional checks at each time step.

        :param flight_point:
        :return: None if Ok, or an error message otherwise
        """

        if not self.mach_bounds[0] <= flight_point.mach <= self.mach_bounds[1]:
            return f"true_airspeed value {flight_point.true_airspeed:.1f}m/s is out of bound."
        if not self.altitude_bounds[0] <= flight_point.altitude <= self.altitude_bounds[1]:
            return f"Altitude value {flight_point.altitude:.0f}m is out of bound."
        if flight_point.mass <= 0.0:
            return "Negative mass value."

    def _add_new_flight_point(self, flight_points: List[FlightPoint], time_step):
        """
        Appends a new flight point to provided flight point list.

        :param flight_points: list of previous flight points, modified in place.
        :param time_step: time step for new computed flight point.
        """
        new_point = self.compute_next_flight_point(flight_points, time_step)
        self.complete_flight_point(new_point)
        flight_points.append(new_point)

    @staticmethod
    def _compute_next_altitude(next_point: FlightPoint, previous_point: FlightPoint):
        time_step = next_point.time - previous_point.time
        next_point.altitude = (
            previous_point.altitude
            + time_step * previous_point.true_airspeed * np.sin(previous_point.slope_angle)
        )

    def _get_optimal_altitude(
        self, mass: float, mach: float, altitude_guess: float = None
    ) -> float:
        """
        Computes optimal altitude for provided mass and Mach number.

        :param mass:
        :param mach:
        :return: altitude that matches optimal CL
        """

        if altitude_guess is None:
            altitude_guess = 10000.0

        def distance_to_optimum(altitude):
            atm = self._get_atmosphere_point(altitude)
            true_airspeed = mach * atm.speed_of_sound
            optimal_air_density = (
                2.0 * mass * g / (self.reference_area * true_airspeed ** 2 * self.polar.optimal_cl)
            )
            return (atm.density - optimal_air_density) * 100.0

        optimal_altitude = root_scalar(
            distance_to_optimum, x0=altitude_guess, x1=altitude_guess - 1000.0
        ).root

        return optimal_altitude


@deprecated(
    "Class FlightSegment will be removed in version 2.0. "
    "It is replaced by class AbstractTimeStepFlightSegment."
)
@dataclass
class FlightSegment(AbstractTimeStepFlightSegment, ABC):
    """
    Base class for time step computation flight segments.

    This class implements the time computation. For this computation to work, subclasses must
    implement abstract methods :meth:`get_get_distance_to_target`,
    :meth:`get_gamma_and_acceleration` and :meth:`compute_propulsion`.
    """


@dataclass
class AbstractManualThrustSegment(AbstractTimeStepFlightSegment, ABC):
    """
    Base class for computing flight segment where thrust rate is imposed.

    :ivar thrust_rate: used thrust rate. Can be set at instantiation using a keyword argument.
    """

    thrust_rate: float = 1.0

    def compute_propulsion(self, flight_point: FlightPoint):
        flight_point.thrust_rate = self.thrust_rate
        flight_point.thrust_is_regulated = False
        self.propulsion.compute_flight_points(flight_point)


@dataclass
class AbstractRegulatedThrustSegment(AbstractTimeStepFlightSegment, ABC):
    """
    Base class for computing flight segment where thrust rate is adjusted on drag.
    """

    time_step: float = 60.0

    def __post_init__(self):
        super().__post_init__()
        self.target.mach = self.CONSTANT_VALUE

    def compute_propulsion(self, flight_point: FlightPoint):
        flight_point.thrust = flight_point.drag
        flight_point.thrust_is_regulated = True
        self.propulsion.compute_flight_points(flight_point)

    def get_gamma_and_acceleration(self, flight_point: FlightPoint) -> Tuple[float, float]:
        return 0.0, 0.0


@dataclass
class AbstractFixedDurationSegment(AbstractTimeStepFlightSegment, ABC):
    """
    Base class for computing a fixed-duration segment.
    """

    time_step: float = 60.0

    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:
        current = flight_points[-1]
        return target.time - current.time
