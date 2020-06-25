"""Computation of flight path segments."""
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
from abc import abstractmethod, ABC
from typing import Tuple, List

import numpy as np
import pandas as pd
from fastoad.constants import FlightPhase
from fastoad.models.propulsion import IPropulsion
from fastoad.utils.physics import Atmosphere
from numpy import ndarray
from scipy.constants import g
from scipy.interpolate import interp1d
from scipy.optimize import fmin, root_scalar

_LOGGER = logging.getLogger(__name__)  # Logger for this module

DEFAULT_TIME_STEP = 0.5


class Polar:
    def __init__(
        self, cl: ndarray, cd: ndarray,
    ):
        """
        Class for managing aerodynamic polar data.

        Links drag coefficient (CD) to lift coefficient (CL).
        It is defined by two vectors with CL and CD values.

        Once defined, for any CL value, CD can be obtained using :meth:`cd`.

        :param cl: a N-elements array with CL values
        :param cd: a N-elements array with CD values that match CL
        """
        self._definition_CL = cl
        self._cd = interp1d(cl, cd, kind="quadratic", fill_value="extrapolate")

        def _negated_lift_drag_ratio(lift_coeff):
            """returns -CL/CD"""
            return -lift_coeff / self.cd(lift_coeff)

        self._optimal_CL = fmin(_negated_lift_drag_ratio, cl[0])

    @property
    def definition_cl(self):
        """The vector that has been used for defining lift coefficient."""
        return self._definition_CL

    @property
    def optimal_cl(self):
        """The CL value that provides larger lift/drag ratio."""
        return self._optimal_CL

    def cd(self, cl):
        """
        Computes drag coefficient (CD) by interpolation in definition data.

        :param cl: lift coefficient (CL) values
        :return: CD values for each provide CL values
        """
        return self._cd(cl)


class FlightPoint(dict):
    """
    Class for storing data for one flight point.

    An instance is a simple dict, but for convenience, each item can be accessed
    as an attribute (inspired by pandas DataFrames). Hence, one can write::

        >>> fp = FlightPoint(speed=250., altitude=10000.)
        >>> fp["speed"]
        250.0
        >>> fp2 = FlightPoint({"speed":150., "altitude":5000.})
        >>> fp2.speed
        250.0
        >>> fp["mass"] = 70000.
        >>> fp.mass
        70000.0
        >>> fp.mass = 50000.
        >>> fp["mass"]
        50000.0

    Note: constructor will forbid usage of unknown keys, but other methods will
    allow them, while not making the matching between dict keys and attributes,
    hence::

        >>> fp["foo"] = 42  # Ok
        >>> bar = fp.foo  # raises exception !!!!
        >>> fp.foo = 50  # allowed by Python
        >>> # But inner dict is not affected:
        >>> fp.foo
        50
        >>> fp["foo"]
        42

    This class is especially useful for generating pandas DataFrame: a pandas
    DataFrame can be generated from a list of dict... or a list of FlightPoint
    instances.

    List of dictionary keys that are mapped to instance attributes is given by
    the :attr:`labels` class attribute.
    """

    # List of dictionary keys that are mapped to instance attributes.
    labels = [
        "time",  # in seconds
        "altitude",  # in meters
        "speed",  # in m/s
        "mass",  # in kg
        "ground_distance",  # in m.
        "CL",
        "CD",
        "flight_phase",  # FlightPhase value
        "mach",
        "thrust",  # in Newtons
        "thrust_rate",
        "sfc",  # in kg/N/s
        "slope_angle",  # in radians
        "acceleration",  # in m/s**2
    ]

    def __init__(self, *args, **kwargs):
        """

        :param args: a dict-like object where all keys are contained in :attr:`labels`
        :param kwargs: must be name contained in :attr:`labels`
        """
        super().__init__(*args, **kwargs)
        for key in self:
            if key not in self.labels:
                raise KeyError('"%s" is not a valid key for FlightPoint constructor.' % key)

        # When going from FlightPoint to DataFrame, None values become NaN.
        # But in the other side, NaN values will stay NaN, so, if some fields are
        # not set, we would not have:
        # >>> flight_point == FlightPoint(pd.DataFrame([flight_point]).iloc[0])
        # So we remove NaN values to ensure the equality above in any case.
        for key in self.labels:
            try:
                if key in self and np.isnan(self[key]):
                    del self[key]
            except TypeError:
                pass  # if there has been a type error, then self[key] is not NaN

    def __getattr__(self, name):
        if name in self.labels:
            return self.get(name)
        else:
            return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if hasattr(super(), name):
            super().__setattr__(name, value)
        else:
            self[name] = value


class AbstractSegment(ABC):
    """
    Base class for flight path segment.

    Behaviour can be modified using following instance attributes (can be set at
    instantiation using corresponding keyword arguments):

    :ivar time_step: used time step for computation (actual time step can be lower at
                     some particular times of the flight path).
    :ivar flight_phase: the :class:`FlightPhase` value associated to the segment. Can be
                        used in the propulsion model.
    :ivar altitude_bounds: minimum and maximum authorized altitude values. Process will be
                           stopped if computed altitude gets beyond these limits.
    :ivar speed_bounds: minimum and maximum authorized speed values. Process will be
                        stopped if computed altitude gets beyond these limits.
    """

    _keyword_args = {
        "time_step": DEFAULT_TIME_STEP,
        "flight_phase": FlightPhase.CLIMB,
        "altitude_bounds": (-100.0, 40000.0),
        "speed_bounds": (0.0, 1000.0),
    }

    def __init__(self, propulsion: IPropulsion, polar: Polar, reference_surface: float, **kwargs):
        """
        :param propulsion: the propulsion model
        :param polar: the aerodynamic polar
        :param reference_surface: the reference surface for aerodynamic forces
        """
        self.propulsion = propulsion
        self.polar = polar
        self.reference_surface = reference_surface

        for attr_name, default_value in self._keyword_args.items():
            setattr(self, attr_name, kwargs.get(attr_name, default_value))

    def compute(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        """
        Computes the flight path segment from provided start point to provide target point.

        :param start: the initial flight point, defined for speed, altitude and mass
        :param target: the target flight point, defined for any relevant parameter
        :return: a pandas DataFrame where columns are given by :attr:`FlightPoint.labels`
        """
        start = FlightPoint(start)
        if start.time is None:
            start.time = 0.0
        if start.ground_distance is None:
            start.ground_distance = 0.0
        self._complete_flight_point(start)

        target = FlightPoint(target)

        flight_points = [start]

        while not self.target_is_attained(flight_points, target):
            current = flight_points[-1]
            new = self._compute_next_flight_point(current, target)
            self._complete_flight_point(new)
            if not self.speed_bounds[0] <= new.speed <= self.speed_bounds[1]:
                raise ValueError("Speed value %f.1m/s is out of bound. Process stopped.")
            if not self.altitude_bounds[0] <= new.altitude <= self.altitude_bounds[1]:
                raise ValueError("Altitude value %.0fm is out of bound. Process stopped.")

            flight_points.append(new)

        flight_points_df = pd.DataFrame(flight_points)

        return flight_points_df

    @abstractmethod
    def target_is_attained(self, flight_points: List[FlightPoint], target: FlightPoint) -> bool:
        """
        Tells if computation should continue or be halted

        :param flight_points: list of all currently computed flight_points
        :param target: definition of target flight point
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
            speed = mach * atm.speed_of_sound
            optimal_air_density = (
                2.0 * mass * g / (self.reference_surface * speed ** 2 * self.polar.optimal_cl)
            )
            return (atm.density - optimal_air_density) * 100.0

        optimal_altitude = root_scalar(
            distance_to_optimum, x0=altitude_guess, x1=altitude_guess - 1000.0
        ).root

        return optimal_altitude

    @abstractmethod
    def _complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point.

        Assumes that it is already defined for time, altitude, speed and mass.

        :param flight_point: the flight point that will be completed in-place
        """
        pass

    @abstractmethod
    def _compute_next_flight_point(self, previous: FlightPoint, target: FlightPoint) -> FlightPoint:
        """
        Computes time, altitude, speed, mass and ground distance of next flight point.

        :param previous: previous flight point
        :param target: target of the flight segment
        :return: the computed next flight point
        """
        pass


class OptimalCruiseSegment(AbstractSegment):
    """
    Class for computing flight segment at maximum lift/drag ratio.

    Mach is considered constant. Altitude is set to get the optimum CL according
    to current mass.
    """

    def __init__(self, *args, **kwargs):
        """

        :ivar cruise_mach: used thrust rate. Can be set at instantiation using a
                           keyword argument.
        """

        if "cruise_mach" in kwargs:
            self.cruise_mach = kwargs.pop("cruise_mach")

        super().__init__(*args, **kwargs)

    def compute(self, start: FlightPoint, target_ground_distance: float) -> pd.DataFrame:
        """
        Computes the flight path segment from provided start point to provided ground distance.

        :param start: the initial flight point, defined for speed, altitude and mass
        :param target_ground_distance: the target ground distance to cover
        :return: a pandas DataFrame where columns are given by :attr:`FlightPoint.labels`
        """
        target = FlightPoint()
        target.ground_distance = target_ground_distance + start.ground_distance
        return super().compute(start, target)

    def target_is_attained(self, flight_points: List[FlightPoint], target: FlightPoint) -> bool:
        current = flight_points[-1]
        return np.abs(current.ground_distance - target.ground_distance) <= 1.0

    def _complete_flight_point(self, flight_point: FlightPoint):
        """
        Computes data for provided flight point.

        Assumes that it is already defined for time and mass.

        :param flight_point: the flight point that will be completed in-place
        """

        flight_point.altitude = self._get_optimal_altitude(
            flight_point.mass, self.cruise_mach, flight_point.altitude
        )
        atm = Atmosphere(flight_point.altitude, altitude_in_feet=False)
        flight_point.mach = self.cruise_mach
        flight_point.speed = atm.speed_of_sound * flight_point.mach

        flight_point.flight_phase = self.flight_phase

        reference_force = 0.5 * atm.density * flight_point.speed ** 2 * self.reference_surface
        flight_point.CL = flight_point.mass * g / reference_force
        flight_point.CD = self.polar.cd(flight_point.CL)
        drag = flight_point.CD * reference_force

        (
            flight_point.sfc,
            flight_point.thrust_rate,
            flight_point.thrust,
        ) = self.propulsion.compute_flight_points(
            flight_point.mach, flight_point.altitude, flight_point.flight_phase, thrust=drag
        )
        flight_point.slope_angle, flight_point.acceleration = 0.0, 0.0

    def _compute_next_flight_point(self, previous: FlightPoint, target: FlightPoint) -> FlightPoint:
        next_point = FlightPoint()

        time_step = (target.ground_distance - previous.ground_distance) / previous.speed
        time_step = min(self.time_step, time_step)

        next_point.mass = previous.mass - previous.sfc * previous.thrust * time_step
        next_point.mach = self.cruise_mach
        next_point.altitude = (
            previous.altitude
        )  # will provide an initial guess for computing optimal altitude

        next_point.time = previous.time + time_step
        next_point.ground_distance = previous.ground_distance + previous.speed * time_step
        return next_point


class ManualThrustSegment(AbstractSegment, ABC):
    """
    Base class for computing flight segment where thrust rate is imposed.
    """

    def __init__(self, *args, **kwargs):
        """

        :ivar thrust_rate: used thrust rate. Can be set at instantiation using a keyword argument.
        """
        self._keyword_args["thrust_rate"] = 1.0

        super().__init__(*args, **kwargs)

    def _complete_flight_point(self, flight_point: FlightPoint):
        atm = Atmosphere(flight_point.altitude, altitude_in_feet=False)
        reference_force = 0.5 * atm.density * flight_point.speed ** 2 * self.reference_surface

        flight_point.flight_phase = self.flight_phase
        flight_point.mach = flight_point.speed / atm.speed_of_sound
        (
            flight_point.sfc,
            flight_point.thrust_rate,
            flight_point.thrust,
        ) = self.propulsion.compute_flight_points(
            flight_point.mach,
            flight_point.altitude,
            flight_point.flight_phase,
            thrust_rate=self.thrust_rate,
        )
        flight_point.CL = flight_point.mass * g / reference_force
        flight_point.CD = self.polar.cd(flight_point.CL)
        drag = flight_point.CD * reference_force
        flight_point.slope_angle, flight_point.acceleration = self.get_gamma_and_acceleration(
            flight_point.mass, drag, flight_point.thrust
        )

    def _compute_next_flight_point(self, previous: FlightPoint, target: FlightPoint) -> FlightPoint:
        next_point = FlightPoint()
        speed_time_step = altitude_time_step = self.time_step
        if previous.acceleration != 0.0:
            speed_time_step = (target.speed - previous.speed) / previous.acceleration
            if speed_time_step < 0.0:
                _LOGGER.warning(
                    "Incorrect acceleration (%.2f) at %s" % (previous.acceleration, previous)
                )
                speed_time_step = self.time_step
        if previous.slope_angle != 0.0:
            altitude_time_step = (
                (target.altitude - previous.altitude)
                / previous.speed
                / np.sin(previous.slope_angle)
            )

            if altitude_time_step < 0.0:
                _LOGGER.warning(
                    "Incorrect slope (%.2f°) at %s" % (np.degrees(previous.slope_angle), previous)
                )
                altitude_time_step = self.time_step
        time_step = min(self.time_step, speed_time_step, altitude_time_step)
        next_point.altitude = previous.altitude + time_step * previous.speed * np.sin(
            previous.slope_angle
        )
        next_point.speed = previous.speed + time_step * previous.acceleration
        next_point.mass = previous.mass - previous.sfc * previous.thrust * time_step
        next_point.time = previous.time + time_step
        next_point.ground_distance = previous.ground_distance + previous.speed * time_step * np.cos(
            previous.slope_angle
        )
        return next_point

    @abstractmethod
    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        """
        Computes slope angle (gamma) and acceleration.

        :param mass: in kg
        :param drag: in N
        :param thrust: in N
        :return: slope angle in radians and acceleration in m**2/s
        """


class AccelerationSegment(ManualThrustSegment):
    """
    Computes a flight path segment where speed is modified with no change in altitude.
    """

    def compute(self, start: FlightPoint, target_speed: float) -> pd.DataFrame:
        """
        Computes the flight path segment from provided start point to provides target speed.


        :param start: the initial flight point, defined for speed, altitude and mass
        :param target_speed: the target speed
        :return: a pandas DataFrame where columns are given by :attr:`FlightPoint.labels`
        """
        target = FlightPoint()
        target.speed = target_speed
        return super().compute(start, target)

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        acceleration = (thrust - drag) / mass
        return 0.0, acceleration

    def target_is_attained(self, flight_points: List[FlightPoint], target: FlightPoint) -> bool:
        tol = 1.0e-7  # Such accuracy is not needed, but ensures reproducibility of results.
        return np.abs(flight_points[-1].speed - target.speed) <= tol


class ClimbSegment(ManualThrustSegment):
    """
    Computes a flight path segment where altitude is modified with no change in speed.
    """

    #: Using this value will tell tell to target the altitude with max lift/drag ratio.
    OPTIMAL_ALTITUDE = -10000.0

    def compute(self, start: FlightPoint, target_altitude: float) -> pd.DataFrame:
        """
        Computes the flight path segment from provided start point to provides target altitude.

        If :attr:`OPTIMAL_ALTITUDE` is given as target, segment will stop when
        maximum lift/drag ratio is attained.

        :param start: the initial flight point, defined for speed, altitude and mass
        :param target_altitude: the target altitude
        :return: a pandas DataFrame where columns are given by :attr:`FlightPoint.labels`
        """
        target = FlightPoint()
        if target_altitude == self.OPTIMAL_ALTITUDE:
            target.CL = "optimal"
        else:
            target.altitude = target_altitude

        return super().compute(start, target)

    def get_gamma_and_acceleration(self, mass, drag, thrust) -> Tuple[float, float]:
        gamma = (thrust - drag) / mass / g
        return gamma, 0.0

    def target_is_attained(self, flight_points: List[FlightPoint], target: FlightPoint) -> bool:
        current = flight_points[-1]
        if target.CL == "optimal":
            target.altitude = self._get_optimal_altitude(
                current.mass, current.mach, current.altitude
            )

        tol = 1.0e-7  # Such accuracy is not needed, but ensures reproducibility of results.
        return np.abs(current.altitude - target.altitude) <= tol
