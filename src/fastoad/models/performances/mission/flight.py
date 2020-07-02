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

from typing import Dict

import pandas as pd
from fastoad.constants import FlightPhase, EngineSetting
from fastoad.models.propulsion import IPropulsion
from scipy.constants import foot, knot
from scipy.optimize import root_scalar

from .flight_point import FlightPoint
from .polar import Polar
from .segments.acceleration import AccelerationSegment, DecelerationSegment
from .segments.climb_descent import ClimbSegment, DescentSegment
from .segments.cruise import OptimalCruiseSegment


class Flight:

    """
    
    """

    def __init__(
        self,
        propulsion: IPropulsion,
        reference_surface: float,
        low_speed_polar: Polar,
        high_speed_polar: Polar,
        cruise_mach: float,
        thrust_rates: Dict[FlightPhase, float],
        cruise_distance: float,
    ):

        self.segment_low_speed_args = propulsion, reference_surface, low_speed_polar
        self.segment_high_speed_args = propulsion, reference_surface, high_speed_polar
        self.cruise_mach = cruise_mach
        self.thrust_rates = thrust_rates
        self.cruise_distance = cruise_distance

    def get_flight_sequence(self):
        return [
            # Initial climb ====================================================
            ClimbSegment(
                FlightPoint(true_airspeed="constant", altitude=400.0 * foot),
                *self.segment_low_speed_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
            ),
            AccelerationSegment(
                FlightPoint(equivalent_airspeed=250.0 * knot),
                *self.segment_low_speed_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
            ),
            ClimbSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=1500.0 * foot),
                *self.segment_low_speed_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
            ),
            # Climb ============================================================
            ClimbSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=10000.0 * foot),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.CLIMB],
                engine_setting=EngineSetting.CLIMB,
            ),
            AccelerationSegment(
                FlightPoint(equivalent_airspeed=300.0 * knot),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.CLIMB],
                engine_setting=EngineSetting.CLIMB,
            ),
            ClimbSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=ClimbSegment.OPTIMAL_ALTITUDE),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.CLIMB],
                cruise_mach=self.cruise_mach,
                engine_setting=EngineSetting.CLIMB,
            ),
            # Cruise ===========================================================
            OptimalCruiseSegment(
                FlightPoint(ground_distance=self.cruise_distance),
                *self.segment_high_speed_args,
                cruise_mach=self.cruise_mach,
                engine_setting=EngineSetting.CRUISE,
            ),
            # Descent ==========================================================
            DescentSegment(
                FlightPoint(equivalent_airspeed=300.0 * knot, mach="constant"),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
            ),
            DescentSegment(
                FlightPoint(altitude=10000.0 * foot, equivalent_airspeed="constant"),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
            ),
            DecelerationSegment(
                FlightPoint(equivalent_airspeed=250.0 * knot),
                *self.segment_high_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
            ),
            DescentSegment(
                FlightPoint(altitude=1500.0 * foot, equivalent_airspeed="constant"),
                *self.segment_low_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
            ),
        ]

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        flight_sequence = self.get_flight_sequence()
        segment_start = start
        segments = []
        for segment_calculator in flight_sequence:
            print(segment_calculator)
            segments.append(segment_calculator.compute(segment_start))
            segment_start = FlightPoint(segments[-1].iloc[-1])
            print(segment_start)

        return pd.concat(segments)


class RangedFlight(Flight):
    def __init__(
        self,
        propulsion: IPropulsion,
        reference_surface: float,
        low_speed_polar: Polar,
        high_speed_polar: Polar,
        cruise_mach: float,
        thrust_rates: Dict[FlightPhase, float],
        range: float,
    ):
        self.range = range
        self.flight = Flight(
            propulsion,
            reference_surface,
            low_speed_polar,
            high_speed_polar,
            cruise_mach,
            thrust_rates,
            range,
        )
        self.flight_points = None

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        def compute_flight(cruise_distance):
            self.flight.cruise_distance = cruise_distance
            self.flight_points = self.flight.compute(start)
            obtained_range = self.flight_points.iloc[-1].ground_distance
            return self.range - obtained_range

        needed_cruise_range = root_scalar(compute_flight, x0=self.range, x1=self.range * 0.5).root
        print(needed_cruise_range)
        return self.flight_points
