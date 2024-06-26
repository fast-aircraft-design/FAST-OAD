"""Base classes for time-step segments"""
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

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from deprecated import deprecated
from scipy.constants import g
from scipy.optimize import root_scalar

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from fastoad.model_base.propulsion import IPropulsion
from .base import AbstractFlightSegment
from ..polar import Polar
from ..polar_modifier import AbstractPolarModifier, UnchangedPolar

DEFAULT_TIME_STEP = 0.2

_LOGGER = logging.getLogger(__name__)  # Logger for this module


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

    :meth:`compute_next_alpha` also has to be overloaded if angle of attack should be
    different of 0.
    """

    #: A IPropulsion instance that will be called at each time step.
    propulsion: IPropulsion = MANDATORY_FIELD

    #: The Polar instance that will provide drag data.
    polar: Polar = MANDATORY_FIELD

    #: A polar modifier that can apply dynamic changes to the original polar
    # (the default value returns a polar without change)
    polar_modifier: AbstractPolarModifier = field(default_factory=UnchangedPolar)

    #: The reference area, in m**2.
    reference_area: float = MANDATORY_FIELD

    #: Used time step for computation (actual time step can be lower at some particular times of
    #: the flight path).
    time_step: float = DEFAULT_TIME_STEP

    # The maximum lift coefficient for optimal climb and cruise segments
    maximum_CL: float = None

    #: Minimum and maximum authorized altitude values. If computed altitude gets beyond these
    #: limits, computation will be interrupted and a warning message will be issued in logger.
    altitude_bounds: tuple = (-500.0, 40000.0)

    #: Minimum and maximum authorized mach values. If computed Mach gets beyond these limits,
    #: computation will be interrupted and a warning message will be issued in logger.
    mach_bounds: tuple = (-1.0e-6, 5.0)

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

    def get_next_alpha(
        self, previous_point: FlightPoint, time_step: float  # pylint: disable=unused-argument
    ) -> float:
        """
        Determine the next angle of attack.

        :param previous_point: the flight point from which next alpha is computed
        :param time_step: the duration between computed flight point and previous_point
        """
        return 0.0

    def complete_flight_point(self, flight_point: FlightPoint):
        super().complete_flight_point(flight_point)
        if flight_point.altitude is not None:
            atm = self._get_atmosphere_point(flight_point.altitude)
            reference_force = (
                0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_area
            )

            if self.polar:
                modified_polar = self.polar_modifier.modify_polar(self.polar, flight_point)
                flight_point.CL = flight_point.mass * g / reference_force
                flight_point.CD = modified_polar.cd(flight_point.CL)
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

            if (
                np.abs(last_point_to_target) > tol
                and last_point_to_target * previous_point_to_target < 0.0
            ):

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

                rtol = tol
                while np.abs(last_point_to_target) > tol:
                    rtol *= 0.1
                    root_scalar(
                        replace_last_point,
                        x0=self.time_step,
                        x1=self.time_step / 2.0,
                        rtol=rtol,
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
                _LOGGER.warning('%s Segment computation interrupted in "%s".', msg, self.name)
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

        next_point.isa_offset = self.isa_offset
        consumed_mass = self.propulsion.get_consumed_mass(previous, time_step)
        next_point.mass = previous.mass - consumed_mass
        next_point.consumed_fuel = previous.consumed_fuel + consumed_mass

        next_point.time = previous.time + time_step
        next_point.ground_distance = (
            previous.ground_distance
            + previous.true_airspeed * time_step * np.cos(previous.slope_angle)
        )
        next_point.alpha = self.get_next_alpha(previous, time_step)
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

    def _check_values(self, flight_point: FlightPoint) -> Optional[str]:
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
        return None

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
            if self.maximum_CL is not None:
                CL_optimal = min(self.polar.optimal_cl, self.maximum_CL)
            else:
                CL_optimal = self.polar.optimal_cl
            optimal_air_density = (
                2.0 * mass * g / (self.reference_area * true_airspeed ** 2 * CL_optimal)
            )
            return (atm.density - optimal_air_density) * 100.0

        optimal_altitude = root_scalar(
            distance_to_optimum, x0=altitude_guess, x1=altitude_guess - 1000.0
        ).root

        return optimal_altitude


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


@dataclass
class AbstractTakeOffSegment(AbstractManualThrustSegment, ABC):
    """
    Class for computing takeoff segment.
    """

    # Default time step for this dynamic segment
    time_step: float = 0.1

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        self.polar_modifier.ground_altitude = start.altitude
        return super().compute_from_start_to_target(start, target)


@dataclass
class AbstractGroundSegment(AbstractTakeOffSegment, ABC):
    """
    Class for computing accelerated segments on the ground with wheel friction.
    """

    # Friction coefficient considered for acceleration at take-off.
    # The default value is representative of dry concrete/asphalte
    wheels_friction: float = 0.03

    def get_gamma_and_acceleration(self, flight_point: FlightPoint):
        """
        For ground segment, gamma is assumed always 0 and wheel friction
        (with or without brake) is added to drag
        """
        mass = flight_point.mass
        drag_aero = flight_point.drag
        lift = flight_point.lift
        thrust = flight_point.thrust

        drag = drag_aero + (mass * g - lift) * self.wheels_friction

        # edit flight_point fields
        flight_point.drag = drag

        acceleration = (thrust - drag) / mass

        return 0.0, acceleration

    def complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point using AoA and apply polar modification if any

        :param flight_point: the flight point that will be completed in-place
        """
        self._complete_speed_values(flight_point)

        # Ground segment may force engine setting like reverse or idle
        flight_point.engine_setting = self.engine_setting

        atm = self._get_atmosphere_point(flight_point.altitude)
        reference_force = 0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_area

        if self.polar:
            alpha = flight_point.alpha
            modified_polar = self.polar_modifier.modify_polar(self.polar, flight_point)
            flight_point.CL = modified_polar.cl(alpha)
            flight_point.CD = modified_polar.cd(flight_point.CL)
        else:
            flight_point.CL = flight_point.CD = 0.0

        flight_point.drag = flight_point.CD * reference_force
        flight_point.lift = flight_point.CL * reference_force

        self.compute_propulsion(flight_point)
        flight_point.slope_angle, flight_point.acceleration = self.get_gamma_and_acceleration(
            flight_point
        )


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
