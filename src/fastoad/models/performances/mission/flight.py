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

from typing import Dict, List

import pandas as pd
from fastoad.constants import FlightPhase, EngineSetting
from fastoad.models.performances.mission.segments.acceleration import AccelerationSegment
from fastoad.models.performances.mission.segments.base import AbstractSegment
from fastoad.models.performances.mission.segments.cruise import OptimalCruiseSegment
from fastoad.models.propulsion import IPropulsion
from scipy.constants import foot, knot

from ..mission.flight_point import FlightPoint
from ..mission.polar import Polar
from ..mission.segments.climb_descent import ClimbDescentSegment


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

        segment_low_speed_args = propulsion, reference_surface, low_speed_polar
        segment_high_speed_args = propulsion, reference_surface, high_speed_polar

        self.flight_sequence: List[AbstractSegment] = [
            # Initial climb
            ClimbDescentSegment(
                FlightPoint(true_airspeed="constant", altitude=400.0 * foot),
                *segment_low_speed_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
            ),
            AccelerationSegment(
                FlightPoint(equivalent_airspeed=250.0 * knot),
                *segment_low_speed_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
            ),
            ClimbDescentSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=1500.0 * foot),
                *segment_low_speed_args,
                thrust_rate=1.0,
                engine_setting=EngineSetting.TAKEOFF,
            ),
            # Climb
            ClimbDescentSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=10000.0 * foot),
                *segment_high_speed_args,
                thrust_rate=thrust_rates[FlightPhase.CLIMB],
                engine_setting=EngineSetting.CLIMB,
            ),
            AccelerationSegment(
                FlightPoint(equivalent_airspeed=300.0 * knot),
                *segment_high_speed_args,
                thrust_rate=thrust_rates[FlightPhase.CLIMB],
                engine_setting=EngineSetting.CLIMB,
            ),
            ClimbDescentSegment(
                FlightPoint(
                    equivalent_airspeed="constant", altitude=ClimbDescentSegment.OPTIMAL_ALTITUDE
                ),
                *segment_high_speed_args,
                thrust_rate=thrust_rates[FlightPhase.CLIMB],
                cruise_mach=cruise_mach,
                engine_setting=EngineSetting.CLIMB,
            ),
            # Cruise
            OptimalCruiseSegment(
                FlightPoint(ground_distance=cruise_distance),
                *segment_high_speed_args,
                cruise_mach=cruise_mach,
                engine_setting=EngineSetting.CRUISE,
            ),
            # Descent
            ClimbDescentSegment(
                FlightPoint(equivalent_airspeed=300.0 * knot, mach="constant"),
                *segment_high_speed_args,
                thrust_rate=thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
            ),
            # ClimbDescentSegment(
            #     FlightPoint(altitude=10000.0 * foot, equivalent_airspeed="constant"),
            #     *segment_high_speed_args,
            #     thrust_rate=thrust_rates[FlightPhase.DESCENT],
            #     engine_setting=EngineSetting.IDLE,
            # ),
            AccelerationSegment(
                FlightPoint(equivalent_airspeed=250.0 * knot),
                *segment_high_speed_args,
                thrust_rate=thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
            ),
            ClimbDescentSegment(
                FlightPoint(altitude=1500.0 * foot, equivalent_airspeed="constant"),
                *segment_low_speed_args,
                thrust_rate=thrust_rates[FlightPhase.DESCENT],
                engine_setting=EngineSetting.IDLE,
            ),
        ]

    def compute(self, start: FlightPoint) -> pd.DataFrame:
        segment_start = start
        segments = []
        for segment_calculator in self.flight_sequence:
            print(segment_calculator)
            segments.append(segment_calculator.compute(segment_start))
            segment_start = FlightPoint(segments[-1].iloc[-1])
            print(segment_start)

        return pd.concat(segments)
