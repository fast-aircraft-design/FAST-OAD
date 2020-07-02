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
from .segments.altitude_change import AltitudeChangeSegment
from .segments.cruise import OptimalCruiseSegment
from .segments.speed_change import SpeedChangeSegment


class StandardFlight:
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
        time_step=None,
    ):

        self.segment_low_speed_args = propulsion, reference_surface, low_speed_polar
        self.segment_high_speed_args = propulsion, reference_surface, high_speed_polar
        self.cruise_mach = cruise_mach
        self.thrust_rates = thrust_rates
        self.cruise_distance = cruise_distance
        self.time_step = time_step

    def get_flight_sequence(self):
        return [
            # Initial climb ====================================================
            AltitudeChangeSegment(
                FlightPoint(true_airspeed="constant", altitude=400.0 * foot),
                *self.segment_low_speed_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
                time_step=self.time_step,
            ),
            SpeedChangeSegment(
                FlightPoint(equivalent_airspeed=250.0 * knot),
                *self.segment_low_speed_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
                time_step=self.time_step,
            ),
            AltitudeChangeSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=1500.0 * foot),
                *self.segment_low_speed_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
                time_step=self.time_step,
            ),
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
                cruise_mach=self.cruise_mach,
                engine_setting=EngineSetting.CLIMB,
                time_step=self.time_step,
            ),
            # Cruise ===========================================================
            OptimalCruiseSegment(
                FlightPoint(ground_distance=self.cruise_distance),
                *self.segment_high_speed_args,
                cruise_mach=self.cruise_mach,
                engine_setting=EngineSetting.CRUISE,
            ),
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
                *self.segment_low_speed_args,
                thrust_rate=self.thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
                time_step=self.time_step,
            ),
        ]

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        flight_sequence = self.get_flight_sequence()
        segment_start = start
        segments = []
        for segment_calculator in flight_sequence:
            segments.append(segment_calculator.compute(segment_start))
            segment_start = FlightPoint(segments[-1].iloc[-1])

        return pd.concat(segments)


class RangedFlight(StandardFlight):
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
        self.flight = StandardFlight(
            propulsion,
            reference_surface,
            low_speed_polar,
            high_speed_polar,
            cruise_mach,
            thrust_rates,
            range,
            time_step=None,
        )
        self.flight_points = None

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        def compute_flight(cruise_distance):
            self.flight.cruise_distance = cruise_distance
            self.flight_points = self.flight.compute(start)
            obtained_range = self.flight_points.iloc[-1].ground_distance
            return self.range - obtained_range

        needed_cruise_range = root_scalar(
            compute_flight, x0=self.range * 0.5, x1=self.range * 0.25, xtol=0.5e3, method="secant"
        ).root
        print(needed_cruise_range)
        return self.flight_points
