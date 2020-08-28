"""Base classes for simulating flight segments."""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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
from typing import List, Tuple

import numpy as np
import pandas as pd
from scipy.constants import g
from scipy.optimize import root_scalar

from fastoad.base.dict import DynamicAttributeDict, AddKeyAttributes
from fastoad.base.flight_point import FlightPoint
from fastoad.constants import EngineSetting
from fastoad.models.propulsion import IPropulsion
from fastoad.utils.physics import AtmosphereSI
from ..base import IFlightPart
from ..exceptions import FastFlightSegmentIncompleteFlightPoint
from ..polar import Polar

_LOGGER = logging.getLogger(__name__)  # Logger for this module

DEFAULT_TIME_STEP = 0.2

SEGMENT_KEYWORD_ARGUMENTS = {
    "time_step": DEFAULT_TIME_STEP,
    "engine_setting": EngineSetting.CLIMB,
    "altitude_bounds": (-500.0, 40000.0),  # large limits for stopping bad computation
    "mach_bounds": (0.0, 5.0),  # large limits for stopping bad computation
    "maximum_mach": 100.0,  # not limited by default
    "name": "",
}


@AddKeyAttributes(SEGMENT_KEYWORD_ARGUMENTS)
class AbstractSegment(IFlightPart, DynamicAttributeDict):
    """
    Base class for flight path segment.

    Behaviour can be modified using following instance attributes (can be set at
    instantiation using corresponding keyword arguments):

    :ivar time_step: used time step for computation (actual time step can be lower at
                     some particular times of the flight path).
    :ivar engine_setting: the :class:`EngineSetting` value associated to the segment. Can be
                        used in the propulsion model.
    :ivar altitude_bounds: minimum and maximum authorized altitude values. If computed altitude
                           gets beyond these limits, computation will be interrupted and a warning
                           message will be issued in logger.
    :ivar mach_bounds: minimum and maximum authorized mach values. If computed Mach
                       gets beyond these limits, computation will be interrupted and a warning
                       message will be issued in logger.
    :ivar maximum_mach: if defined, this maximum Mach number will be enforced at each time
                        step, whatever the speed specifications.
    :ivar name: the name of the current flight sequence.
    """

    def __init__(
        self,
        *,
        target: FlightPoint,
        propulsion: IPropulsion,
        reference_area: float,
        polar: Polar,
        **kwargs
    ):
        """
        Only keyword arguments are accepted.

        :param target: the target flight point, defined for any relevant parameter
        :param propulsion: the propulsion model
        :param reference_area: the reference area for aerodynamic forces
        :param polar: the aerodynamic polar
        """
        self.propulsion = propulsion
        self.reference_area = reference_area
        self.polar = polar
        self.target = FlightPoint(target)

        # If true, computation will stop if a flight point is further from target
        # than previous one.
        self.interrupt_if_getting_further_from_target = True
        super().__init__(**kwargs)

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        """
        Computes the flight path segment from provided start point.

        Computation ends when target is attained, or if the computation stops getting
        closer to target.
        For instance, a climb computation with too low thrust will only return one
        flight point, that is the provided start point.

        :param start: the initial flight point, defined for `altitude`, `mass` and speed
                      (`true_airspeed`, `equivalent_airspeed` or `mach`). Can also be
                      defined for `time` and/or `ground_distance`.
        :return: a pandas DataFrame where columns are given by :attr:`FlightPoint.labels`
        """
        start = FlightPoint(start)
        if start.time is None:
            start.time = 0.0
        if start.ground_distance is None:
            start.ground_distance = 0.0

        self.complete_flight_point(start)

        flight_points = [start]

        previous_point_to_target = self._get_distance_to_target(flight_points)
        tol = 1.0e-5  # Such accuracy is not needed, but ensures reproducibility of results.
        while np.abs(previous_point_to_target) > tol:
            self._add_new_flight_point(flight_points, self.time_step)
            last_point_to_target = self._get_distance_to_target(flight_points)

            if last_point_to_target * previous_point_to_target < 0.0:

                # Target has been exceeded. Let's look for the exact time step using root_scalar.
                def replace_last_point(time_step):
                    """
                    Replaces last point of flight_points.

                    :param time_step: time step for new point
                    :return: new distance to target
                    """
                    del flight_points[-1]
                    self._add_new_flight_point(flight_points, time_step)
                    return self._get_distance_to_target(flight_points)

                root_scalar(
                    replace_last_point, x0=self.time_step, x1=self.time_step / 2.0, rtol=tol
                )
                last_point_to_target = self._get_distance_to_target(flight_points)
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

    def _check_values(self, flight_point: FlightPoint) -> str:
        """
        Checks that computed values are consistent.

        May be overloaded for doing specific additional checks at each time step.

        :param flight_point:
        :return: None if Ok, or an error message otherwise
        """

        if not self.mach_bounds[0] <= flight_point.mach <= self.mach_bounds[1]:
            return "true_airspeed value %f.1m/s is out of bound." % flight_point.true_airspeed
        if not self.altitude_bounds[0] <= flight_point.altitude <= self.altitude_bounds[1]:
            return "Altitude value %.0fm is out of bound." % flight_point.altitude
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

        if self.target.true_airspeed == "constant":
            next_point.true_airspeed = previous.true_airspeed
        elif self.target.equivalent_airspeed == "constant":
            next_point.equivalent_airspeed = start.equivalent_airspeed
        elif self.target.mach == "constant":
            next_point.mach = start.mach
        else:
            next_point.true_airspeed = previous.true_airspeed + time_step * previous.acceleration

        # The naming is not done in complete_flight_point for not naming the start point
        next_point.name = self.name
        return next_point

    def complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point.

        Assumes that it is already defined for time, altitude, mass,
        ground distance and speed (TAS, EAS, or Mach).

        :param flight_point: the flight point that will be completed in-place
        """
        flight_point.engine_setting = self.engine_setting

        self._complete_speed_values(flight_point)
        # Mach number is capped by self.maximum_mach
        if flight_point.mach > self.maximum_mach:
            flight_point.mach = self.maximum_mach
            flight_point.true_airspeed = flight_point.equivalent_airspeed = None
            self._complete_speed_values(flight_point)

        atm = AtmosphereSI(flight_point.altitude)
        reference_force = 0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_area

        if self.polar:
            flight_point.CL = flight_point.mass * g / reference_force
            flight_point.CD = self.polar.cd(flight_point.CL)
        else:
            flight_point.CL = flight_point.CD = 0.0
        flight_point.drag = flight_point.CD * reference_force

        self._compute_propulsion(flight_point)
        flight_point.slope_angle, flight_point.acceleration = self._get_gamma_and_acceleration(
            flight_point.mass, flight_point.drag, flight_point.thrust
        )

    @staticmethod
    def _complete_speed_values(flight_point: FlightPoint):
        """
        Computes consistent values between TAS, EAS and Mach, assuming one of them is defined.
        """
        atm = AtmosphereSI(flight_point.altitude)

        if flight_point.true_airspeed is None:
            if flight_point.mach:
                flight_point.true_airspeed = flight_point.mach * atm.speed_of_sound
            elif flight_point.equivalent_airspeed:
                flight_point.true_airspeed = atm.get_true_airspeed(flight_point.equivalent_airspeed)
            else:
                raise FastFlightSegmentIncompleteFlightPoint(
                    "Flight point should be defined for true_airspeed, "
                    "equivalent_airspeed, or mach."
                )
        if flight_point.mach is None:
            flight_point.mach = flight_point.true_airspeed / atm.speed_of_sound

        if flight_point.equivalent_airspeed is None:
            flight_point.equivalent_airspeed = atm.get_equivalent_airspeed(
                flight_point.true_airspeed
            )

    @staticmethod
    def _compute_next_altitude(next_point, previous_point):
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
            atm = AtmosphereSI(altitude)
            true_airspeed = mach * atm.speed_of_sound
            optimal_air_density = (
                2.0 * mass * g / (self.reference_area * true_airspeed ** 2 * self.polar.optimal_cl)
            )
            return (atm.density - optimal_air_density) * 100.0

        optimal_altitude = root_scalar(
            distance_to_optimum, x0=altitude_guess, x1=altitude_guess - 1000.0
        ).root

        return optimal_altitude

    @abstractmethod
    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> bool:
        """
        Computes a "distance" from last flight point to target.

        Computed does not need to have a real meaning.
        The important point is that it must be signed so that algorithm knows on
        which "side" of the target we are.
        And of course, it should be 0. if flight point is on target.

        :param flight_points: list of all currently computed flight_points
        :return: O. if target is attained, a non-null value otherwise
        """

    @abstractmethod
    def _get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        """
        Computes slope angle (gamma) and acceleration.

        :param mass: in kg
        :param drag: in N
        :param thrust: in N
        :return: slope angle in radians and acceleration in m**2/s
        """

    @abstractmethod
    def _compute_propulsion(self, flight_point: FlightPoint):
        """
        Computes propulsion data.

        Provided flight point is modified in place.

        :param flight_point:
        """


@AddKeyAttributes({"thrust_rate": 1.0})
class ManualThrustSegment(AbstractSegment, ABC):
    """
    Base class for computing flight segment where thrust rate is imposed.

    :ivar thrust_rate: used thrust rate. Can be set at instantiation using a keyword argument.
    """

    def _compute_propulsion(self, flight_point: FlightPoint):
        flight_point.thrust_rate = self.thrust_rate
        flight_point.thrust_is_regulated = False
        self.propulsion.compute_flight_points(flight_point)


@AddKeyAttributes({"time_step": 60.0})
class RegulatedThrustSegment(AbstractSegment, ABC):
    """
    Base class for computing flight segment where thrust rate is adjusted on drag.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target.mach = "constant"

    def _compute_propulsion(self, flight_point: FlightPoint):
        flight_point.thrust = flight_point.drag
        flight_point.thrust_is_regulated = True
        self.propulsion.compute_flight_points(flight_point)

    def _get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        return 0.0, 0.0


class FixedDurationSegment(AbstractSegment, ABC):
    """
    Class for computing phases where duration is fixed.

    Target duration is provide as target.time.
    When using :meth:`compute_from`, if start.time is not 0, end time will be
    start.time + target.time.
    """

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        start = FlightPoint(start)
        if start.time:
            self.target.time = self.target.time + start.time
        return super().compute_from(start)

    def _get_distance_to_target(self, flight_points: List[FlightPoint]) -> bool:
        current = flight_points[-1]
        return self.target.time - current.time
