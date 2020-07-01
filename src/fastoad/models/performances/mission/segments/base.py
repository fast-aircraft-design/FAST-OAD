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
from fastoad.models.propulsion import IPropulsion
from fastoad.utils.physics import AtmosphereSI
from scipy.constants import g
from scipy.optimize import root_scalar

from ..flight_point import FlightPoint
from ..polar import Polar

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
        Computes the flight path segment from provided start point.

        :param start: the initial flight point, defined for altitude, mass and any relevant
                      parameter.
        :return: a pandas DataFrame where columns are given by :attr:`FlightPoint.labels`
        """
        start = FlightPoint(start)
        if start.time is None:
            start.time = 0.0
        if start.ground_distance is None:
            start.ground_distance = 0.0

        self._complete_flight_point(start)

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

            # Check altitude and speed bounds.
            new_point = flight_points[-1]
            if not self.speed_bounds[0] <= new_point.true_airspeed <= self.speed_bounds[1]:
                raise ValueError(
                    "true_airspeed value %f.1m/s is out of bound. Process stopped."
                    % new_point.true_airspeed
                )
            if not self.altitude_bounds[0] <= new_point.altitude <= self.altitude_bounds[1]:
                raise ValueError(
                    "Altitude value %.0fm is out of bound. Process stopped." % new_point.altitude
                )

            previous_point_to_target = last_point_to_target
            flight_points.append(new_point)

        flight_points_df = pd.DataFrame(flight_points)

        return flight_points_df

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
    def _compute_next_flight_point(
        self, flight_points: List[FlightPoint], time_step: float
    ) -> FlightPoint:
        """
        Computes time, altitude, true airspeed, mass and ground distance of next flight point.

        :param flight_points: previous flight points
        :param time_step: time step for computing next point
        :return: the computed next flight point
        """

    @abstractmethod
    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        """
        Computes slope angle (gamma) and acceleration.

        :param mass: in kg
        :param drag: in N
        :param thrust: in N
        :return: slope angle in radians and acceleration in m**2/s
        """

    def _add_new_flight_point(self, flight_points: List[FlightPoint], time_step):
        """
        Appends a new flight point to provided flight point list.

        :param flight_points: list of previous flight points, modified in place.
        :param time_step: time step for new computed flight point.
        """
        new_point = self._compute_next_flight_point(flight_points, time_step)
        self._complete_flight_point(new_point)
        flight_points.append(new_point)

    def _complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point.

        Assumes that it is already defined for time, altitude, true airspeed, mass and
        ground distance.

        :param flight_point: the flight point that will be completed in-place
        """
        self._complete_speed_values(flight_point)

        atm = AtmosphereSI(flight_point.altitude)
        reference_force = (
            0.5 * atm.density * flight_point.true_airspeed ** 2 * self.reference_surface
        )
        flight_point.engine_setting = self.engine_setting

        if self.polar:
            flight_point.CL = flight_point.mass * g / reference_force
            flight_point.CD = self.polar.cd(flight_point.CL)
        else:
            flight_point.CL = flight_point.CD = 0.0
        drag = flight_point.CD * reference_force
        self._compute_propulsion(flight_point, drag)
        flight_point.slope_angle, flight_point.acceleration = self.get_gamma_and_acceleration(
            flight_point.mass, drag, flight_point.thrust
        )

    @abstractmethod
    def _compute_propulsion(self, flight_point: FlightPoint, drag: float):
        """

        :param flight_point:
        :return:
        """

    @staticmethod
    def _complete_speed_values(flight_point: FlightPoint):
        atm = AtmosphereSI(flight_point.altitude)
        if flight_point.true_airspeed is None:
            if flight_point.mach:
                flight_point.true_airspeed = flight_point.mach * atm.speed_of_sound
            elif flight_point.equivalent_airspeed:
                flight_point.true_airspeed = atm.get_true_airspeed(flight_point.equivalent_airspeed)
            else:
                raise ValueError(
                    "Flight point should be defined for true_airspeed, "
                    "equivalent_airspeed, or mach."
                )
        if flight_point.mach is None:
            flight_point.mach = flight_point.true_airspeed / atm.speed_of_sound

        if flight_point.equivalent_airspeed is None:
            flight_point.equivalent_airspeed = atm.get_equivalent_airspeed(
                flight_point.true_airspeed
            )

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
            atm = AtmosphereSI(altitude)
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


class ManualThrustSegment(AbstractSegment, ABC):
    """
    Base class for computing flight segment where thrust rate is imposed.
    """

    def _compute_propulsion(self, flight_point: FlightPoint, drag: float):
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

    def __init__(self, *args, **kwargs):
        """

        :ivar thrust_rate: used thrust rate. Can be set at instantiation using a keyword argument.
        :ivar maximum_mach: maximum Mach number. Can be set at instantiation using a
                           keyword argument.
        """

        self._keyword_args["thrust_rate"] = 1.0
        self._keyword_args["cruise_mach"] = 100.0  # i.e. no limit if not set

        super().__init__(*args, **kwargs)

    def _compute_next_flight_point(
        self, flight_points: List[FlightPoint], time_step: float
    ) -> FlightPoint:
        start = flight_points[0]
        previous = flight_points[-1]
        next_point = FlightPoint()

        next_point.altitude = previous.altitude + time_step * previous.true_airspeed * np.sin(
            previous.slope_angle
        )

        atm = AtmosphereSI(next_point.altitude)
        if self.target.true_airspeed == "constant":
            next_point.true_airspeed = previous.true_airspeed
        elif self.target.equivalent_airspeed == "constant":
            next_point.true_airspeed = atm.get_true_airspeed(start.equivalent_airspeed)
        elif self.target.mach == "constant":
            next_point.true_airspeed = start.mach * atm.speed_of_sound
        else:
            next_point.true_airspeed = previous.true_airspeed + time_step * previous.acceleration

        next_point.mass = previous.mass - previous.sfc * previous.thrust * time_step
        next_point.time = previous.time + time_step
        next_point.ground_distance = (
            previous.ground_distance
            + previous.true_airspeed * time_step * np.cos(previous.slope_angle)
        )
        return next_point
