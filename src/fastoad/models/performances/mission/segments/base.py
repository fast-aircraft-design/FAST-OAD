"""Base classes for simulating flight segments."""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
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

import logging
from abc import ABC, abstractmethod
from typing import List, Tuple

import numpy as np
import pandas as pd
from fastoad.constants import EngineSetting
from fastoad.models.performances.mission.flight_point import FlightPoint
from fastoad.models.performances.mission.polar import Polar
from fastoad.models.propulsion import IPropulsion
from fastoad.utils.physics import Atmosphere
from scipy.constants import g
from scipy.optimize import root_scalar

_LOGGER = logging.getLogger(__name__)  # Logger for this module

DEFAULT_TIME_STEP = 0.2


class AbstractSegment(ABC):

    """
    Base class for flight path segment.

    Behaviour can be modified using following instance attributes (can be set at
    instantiation using corresponding keyword arguments):

    :ivar time_step: used time step for computation (actual time step can be lower at
                     some particular times of the flight path).
    :ivar engine_setting: the :class:`EngineSetting` value associated to the segment. Can be
                        used in the propulsion model.
    :ivar altitude_bounds: minimum and maximum authorized altitude values. Process will be
                           stopped if computed altitude gets beyond these limits.
    :ivar speed_bounds: minimum and maximum authorized true_airspeed values. Process will be
                        stopped if computed altitude gets beyond these limits.
    """

    _keyword_args = {
        "time_step": DEFAULT_TIME_STEP,
        "engine_setting": EngineSetting.CLIMB,
        "altitude_bounds": (-100.0, 40000.0),
        "speed_bounds": (0.0, 1000.0),
    }

    def __init__(
        self,
        target: FlightPoint,
        propulsion: IPropulsion,
        reference_surface: float,
        polar: Polar,
        **kwargs
    ):
        """
        :param target: the target flight point, defined for any relevant parameter
        :param propulsion: the propulsion model
        :param reference_surface: the reference surface for aerodynamic forces
        :param polar: the aerodynamic polar
        """
        self.propulsion = propulsion
        self.reference_surface = reference_surface
        self.polar = polar
        self.target = FlightPoint(target)

        for attr_name, default_value in self._keyword_args.items():
            setattr(self, attr_name, kwargs.get(attr_name, default_value))

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        """
        Computes the flight path segment from provided start point to provide target point.

        :param start: the initial flight point, defined for true_airspeed, altitude and mass
        :return: a pandas DataFrame where columns are given by :attr:`FlightPoint.labels`
        """
        start = FlightPoint(start)
        if start.time is None:
            start.time = 0.0
        if start.ground_distance is None:
            start.ground_distance = 0.0
        self._complete_flight_point(start)

        flight_points = [start]

        while not self.target_is_attained(flight_points):
            current = flight_points[-1]
            new = self._compute_next_flight_point(current)
            self._complete_flight_point(new)
            if not self.speed_bounds[0] <= new.true_airspeed <= self.speed_bounds[1]:
                raise ValueError("true_airspeed value %f.1m/s is out of bound. Process stopped.")
            if not self.altitude_bounds[0] <= new.altitude <= self.altitude_bounds[1]:
                raise ValueError("Altitude value %.0fm is out of bound. Process stopped.")

            flight_points.append(new)

        flight_points_df = pd.DataFrame(flight_points)

        return flight_points_df

    @abstractmethod
    def target_is_attained(self, flight_points: List[FlightPoint]) -> bool:
        """
        Tells if computation should continue or be halted

        :param flight_points: list of all currently computed flight_points
        :return: True if computation should be halted. False otherwise
        """

    def _get_optimal_altitude(
        self, mass: float, mach: float, altitude_guess: float = None
    ) -> Tuple[float, float]:
        """
        Computes optimal altitude for provided mass and Mach number.

        :param mass:
        :param mach:
        :return: altitude that matches optimal CL
        """

        if altitude_guess is None:
            altitude_guess = 10000.0

        def distance_to_optimum(altitude):
            atm = Atmosphere(altitude, altitude_in_feet=False)
            true_airspeed = mach * atm.speed_of_sound
            optimal_air_density = (
                2.0
                * mass
                * g
                / (self.reference_surface * true_airspeed ** 2 * self.polar.optimal_cl)
            )
            return (atm.density - optimal_air_density) * 100.0

        optimal_altitude = root_scalar(
            distance_to_optimum, x0=altitude_guess, x1=altitude_guess - 1000.0
        ).root

        return optimal_altitude

    @abstractmethod
    def _compute_next_flight_point(self, previous: FlightPoint) -> FlightPoint:
        """
        Computes time, altitude, true airspeed, mass and ground distance of next flight point.

        :param previous: previous flight point
        :return: the computed next flight point
        """

    @abstractmethod
    def _complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point.

        Assumes that it is already defined for time, altitude, true airspeed and mass.

        :param flight_point: the flight point that will be completed in-place
        """


class ManualThrustSegment(AbstractSegment, ABC):

    """
    Base class for computing flight segment where thrust rate is imposed.
    """

    def __init__(self, *args, **kwargs):
        """

        :ivar thrust_rate: used thrust rate. Can be set at instantiation using a keyword argument.
        :ivar maximum_mach: maximum Mach number. Can be set at instantiation using a
                           keyword argument.
        """

        self._keyword_args["thrust_rate"] = 1.0
        self._keyword_args["cruise_mach"] = 100.0  # i.e. no limit if not set

        super().__init__(*args, **kwargs)

    def _compute_next_flight_point(self, previous: FlightPoint) -> FlightPoint:
        next_point = FlightPoint()

        # Time step evaluation
        # It will be the minimum value between the estimated time to reach the target and
        # and the default time step.
        # Checks are done against negative time step that could occur if thrust rate
        # creates acceleration when deceleration is needed, and so on...
        # They just create warning, in the (unlikely?) case it is isolated. If we keep
        # getting negative values, the global test about altitude and speed bounds will eventually
        # raise an Exception.
        speed_time_step = altitude_time_step = self.time_step
        if previous.acceleration != 0.0:
            speed_time_step = (
                self.target.true_airspeed - previous.true_airspeed
            ) / previous.acceleration
            if speed_time_step < 0.0:
                _LOGGER.warning(
                    "Incorrect acceleration (%.2f) at %s" % (previous.acceleration, previous)
                )
                speed_time_step = self.time_step
        if previous.slope_angle != 0.0:
            altitude_time_step = (
                (self.target.altitude - previous.altitude)
                / previous.true_airspeed
                / np.sin(previous.slope_angle)
            )

            if altitude_time_step < 0.0:
                _LOGGER.warning(
                    "Incorrect slope (%.2f°) at %s" % (np.degrees(previous.slope_angle), previous)
                )
                altitude_time_step = self.time_step
        time_step = min(self.time_step, speed_time_step, altitude_time_step)

        next_point.altitude = previous.altitude + time_step * previous.true_airspeed * np.sin(
            previous.slope_angle
        )

        if self.target.equivalent_airspeed:
            next_point.true_airspeed = self.get_true_airspeed(
                self.target.equivalent_airspeed, next_point.altitude
            )
        else:
            next_point.true_airspeed = previous.true_airspeed + time_step * previous.acceleration
        next_point.mass = previous.mass - previous.sfc * previous.thrust * time_step
        next_point.time = previous.time + time_step
        next_point.ground_distance = (
            previous.ground_distance
            + previous.true_airspeed * time_step * np.cos(previous.slope_angle)
        )
        return next_point

    def _complete_flight_point(self, flight_point: FlightPoint):

        atm = Atmosphere(flight_point.altitude, altitude_in_feet=False)
        reference_force = (
            0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_surface
        )
        flight_point.engine_setting = self.engine_setting
        flight_point.mach = flight_point.true_airspeed / atm.speed_of_sound
        flight_point.equivalent_airspeed = self.get_equivalent_airspeed(
            flight_point.true_airspeed, flight_point.altitude
        )
        (
            flight_point.sfc,
            flight_point.thrust_rate,
            flight_point.thrust,
        ) = self.propulsion.compute_flight_points(
            flight_point.mach,
            flight_point.altitude,
            flight_point.engine_setting,
            thrust_rate=self.thrust_rate,
        )
        if self.polar:
            flight_point.CL = flight_point.mass * g / reference_force
            flight_point.CD = self.polar.cd(flight_point.CL)
        else:
            flight_point.CL = flight_point.CD = 0.0
        drag = flight_point.CD * reference_force
        flight_point.slope_angle, flight_point.acceleration = self.get_gamma_and_acceleration(
            flight_point.mass, drag, flight_point.thrust
        )

    @abstractmethod
    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        """
        Computes slope angle (gamma) and acceleration.

        :param mass: in kg
        :param drag: in N
        :param thrust: in N
        :return: slope angle in radians and acceleration in m**2/s
        """

    def get_equivalent_airspeed(self, true_airspeed, altitude):
        atm0 = Atmosphere(0)
        atm = Atmosphere(altitude, altitude_in_feet=False)
        return true_airspeed * np.sqrt(atm.density / atm0.density)

    def get_true_airspeed(self, equivalent_airspeed, altitude):
        atm0 = Atmosphere(0)
        atm = Atmosphere(altitude, altitude_in_feet=False)
        return equivalent_airspeed * np.sqrt(atm0.density / atm.density)
