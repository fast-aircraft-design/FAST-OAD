"""Definition of flight missions"""
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

from abc import abstractmethod, ABC
from typing import Dict, List

import pandas as pd
from fastoad.constants import FlightPhase, EngineSetting
from fastoad.models.propulsion import IPropulsion
from scipy.constants import foot, knot
from scipy.optimize import root_scalar

from .flight_point import FlightPoint
from .polar import Polar
from .segments.altitude_change import AltitudeChangeSegment
from .segments.base import AbstractSegment
from .segments.cruise import OptimalCruiseSegment
from .segments.speed_change import SpeedChangeSegment


class AbstractFlight(ABC):
    """
    Defines and computes a flight mission.
    """

    def __init__(
        self,
        propulsion: IPropulsion,
        reference_area: float,
        low_speed_climb_polar: Polar,
        low_speed_descent_polar: Polar,
        high_speed_polar: Polar,
        cruise_mach: float,
        thrust_rates: Dict[FlightPhase, float],
        cruise_distance: float = 0.0,
        time_step=None,
    ):
        """

        :param propulsion:
        :param reference_area:
        :param low_speed_polar:
        :param high_speed_polar:
        :param cruise_mach:
        :param thrust_rates:
        :param cruise_distance: in meters
        :param time_step: if provided, this time step will be applied for all segments.
        """

        self.segment_low_speed_climb_args = propulsion, reference_area, low_speed_climb_polar
        self.segment_low_speed_descent_args = propulsion, reference_area, low_speed_descent_polar
        self.segment_high_speed_args = propulsion, reference_area, high_speed_polar
        self.cruise_mach = cruise_mach
        self.thrust_rates = thrust_rates
        self.cruise_distance = cruise_distance
        self.time_step = time_step

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        """
        Computes the flight mission from provided start point.

        :param start: the initial flight point, defined for altitude, mass and any relevant
                      parameter.
        :return: a pandas DataFrame where columns are given by :attr:`FlightPoint.labels`
        """
        flight_sequence = self.get_flight_sequence()

        # Complete start flight point using first defined flight segment
        flight_sequence[0].complete_flight_point(start)

        segments = [pd.DataFrame([start])]
        for segment_calculator in flight_sequence:
            previous_segment = segments[-1]
            if isinstance(segment_calculator, str):
                previous_segment["tag"] = ""
                previous_segment["tag"].iloc[-1] = segment_calculator
            else:
                segment_start = FlightPoint(previous_segment.iloc[-1])
                flight_points = segment_calculator.compute(segment_start)
                if len(flight_points) > 1:
                    segments.append(flight_points.iloc[1:])

        return pd.concat(segments)

    @abstractmethod
    def get_flight_sequence(self) -> List[AbstractSegment]:
        """
        Defines the mission before calling :meth:`compute`

        It returns a list of AbstractSegment instances and strings. Any string
        is used as a tag for the last point of previous calculated segment.

        A string should not be put as the first element of the list, or behind
        another string element.

        :return: the list of flight segments for the mission.
        """


class StandardFlight(AbstractFlight):
    """
    Defines and computes a standard flight mission, from after takeoff to before landing.
    """

    def get_flight_sequence(self) -> List[AbstractSegment]:
        """

        :return: the list of flight segments for the mission.
        """
        return [
            # Initial climb ====================================================
            AltitudeChangeSegment(
                FlightPoint(true_airspeed="constant", altitude=400.0 * foot),
                *self.segment_low_speed_climb_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
                time_step=self.time_step,
            ),
            SpeedChangeSegment(
                FlightPoint(equivalent_airspeed=250.0 * knot),
                *self.segment_low_speed_climb_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
                time_step=self.time_step,
            ),
            AltitudeChangeSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=1500.0 * foot),
                *self.segment_low_speed_climb_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
                time_step=self.time_step,
            ),
            "End of initial climb",
            # Climb ============================================================
            AltitudeChangeSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=10000.0 * foot),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.CLIMB],
                engine_setting=EngineSetting.CLIMB,
                time_step=self.time_step,
            ),
            SpeedChangeSegment(
                FlightPoint(equivalent_airspeed=300.0 * knot),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.CLIMB],
                engine_setting=EngineSetting.CLIMB,
                time_step=self.time_step,
            ),
            AltitudeChangeSegment(
                FlightPoint(
                    equivalent_airspeed="constant", altitude=AltitudeChangeSegment.OPTIMAL_ALTITUDE
                ),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.CLIMB],
                maximum_mach=self.cruise_mach,
                engine_setting=EngineSetting.CLIMB,
                time_step=self.time_step,
            ),
            "End of climb",
            # Cruise ===========================================================
            OptimalCruiseSegment(
                FlightPoint(ground_distance=self.cruise_distance),
                *self.segment_high_speed_args,
                engine_setting=EngineSetting.CRUISE,
                time_step=self.time_step,
            ),
            "End of cruise",
            # Descent ==========================================================
            AltitudeChangeSegment(
                FlightPoint(equivalent_airspeed=300.0 * knot, mach="constant"),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
                time_step=self.time_step,
            ),
            AltitudeChangeSegment(
                FlightPoint(altitude=10000.0 * foot, equivalent_airspeed="constant"),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
                time_step=self.time_step,
            ),
            SpeedChangeSegment(
                FlightPoint(equivalent_airspeed=250.0 * knot),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
                time_step=self.time_step,
            ),
            AltitudeChangeSegment(
                FlightPoint(altitude=1500.0 * foot, equivalent_airspeed="constant"),
                *self.segment_low_speed_descent_args,
                thrust_rate=self.thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
                time_step=self.time_step,
            ),
            "End of descent",
        ]


class RangedFlight:
    """
    Computes a standard flight mission, from after takeoff to before landing.
    """

    def __init__(
        self, flight_definition: AbstractFlight, flight_distance: float,
    ):
        """
        Computes the flight and adjust the cruise distance to achieve the provided flight distance.

        :param flight_definition:
        :param flight_distance: in meters
        """
        self.flight_distance = flight_distance
        self.flight = flight_definition
        self.flight_points = None
        self.distance_accuracy = 0.5e3

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        def compute_flight(cruise_distance):
            self.flight.cruise_distance = cruise_distance
            self.flight_points = self.flight.compute(start)
            obtained_distance = self.flight_points.iloc[-1].ground_distance
            return self.flight_distance - obtained_distance

        root_scalar(
            compute_flight,
            x0=self.flight_distance * 0.5,
            x1=self.flight_distance * 0.25,
            xtol=0.5e3,
            method="secant",
        )
        return self.flight_points
