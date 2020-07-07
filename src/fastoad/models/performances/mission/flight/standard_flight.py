"""Definition of the standard flight missions."""
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

from typing import Dict, List, Union

from fastoad.constants import FlightPhase, EngineSetting
from fastoad.models.propulsion import IPropulsion
from scipy.constants import foot, knot

from .base import AbstractSimpleFlight
from ..base import IFlightPart, AbstractManualThrustFlightPhase
from ..flight_point import FlightPoint
from ..polar import Polar
from ..segments.altitude_change import AltitudeChangeSegment
from ..segments.cruise import CruiseSegment
from ..segments.speed_change import SpeedChangeSegment


class InitialClimbPhase(AbstractManualThrustFlightPhase):
    """
    Preset for initial climb phase.
    """

    @property
    def flight_sequence(self) -> List[Union[IFlightPart, str]]:
        self.segment_kwargs["engine_setting"] = EngineSetting.CLIMB
        return [
            AltitudeChangeSegment(
                FlightPoint(true_airspeed="constant", altitude=400.0 * foot), **self.segment_kwargs,
            ),
            SpeedChangeSegment(
                FlightPoint(equivalent_airspeed=250.0 * knot), **self.segment_kwargs,
            ),
            AltitudeChangeSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=1500.0 * foot),
                **self.segment_kwargs,
            ),
            "End of initial climb",
        ]


class ClimbPhase(AbstractManualThrustFlightPhase):
    """
    Preset for climb phase.
    """

    @property
    def maximum_mach(self):
        return self._cruise_mach

    @maximum_mach.setter
    def maximum_mach(self, value):
        self._cruise_mach = value

    @property
    def flight_sequence(self) -> List[Union[IFlightPart, str]]:
        self.segment_kwargs["engine_setting"] = EngineSetting.CLIMB
        last_climb = AltitudeChangeSegment(
            FlightPoint(
                equivalent_airspeed="constant", altitude=AltitudeChangeSegment.OPTIMAL_ALTITUDE
            ),
            **self.segment_kwargs,
            maximum_mach=self.maximum_mach,
        )

        return [
            AltitudeChangeSegment(
                FlightPoint(equivalent_airspeed="constant", altitude=10000.0 * foot),
                **self.segment_kwargs,
            ),
            SpeedChangeSegment(
                FlightPoint(equivalent_airspeed=300.0 * knot), **self.segment_kwargs,
            ),
            last_climb,
            "End of climb",
        ]


class DescentPhase(AbstractManualThrustFlightPhase):
    """
    Preset for descent phase.
    """

    @property
    def flight_sequence(self) -> List[Union[IFlightPart, str]]:
        self.segment_kwargs["engine_setting"] = EngineSetting.IDLE
        return [
            AltitudeChangeSegment(
                FlightPoint(equivalent_airspeed=300.0 * knot, mach="constant"),
                **self.segment_kwargs,
            ),
            AltitudeChangeSegment(
                FlightPoint(altitude=10000.0 * foot, equivalent_airspeed="constant"),
                **self.segment_kwargs,
            ),
            SpeedChangeSegment(
                FlightPoint(equivalent_airspeed=250.0 * knot), **self.segment_kwargs,
            ),
            AltitudeChangeSegment(
                FlightPoint(altitude=1500.0 * foot, equivalent_airspeed="constant"),
                **self.segment_kwargs,
            ),
            "End of descent",
        ]


class StandardFlight(AbstractSimpleFlight):
    """
    Defines and computes a standard flight mission, from after takeoff to before landing.
    """

    def __init__(
        self,
        cruise_distance: float,
        propulsion: IPropulsion,
        reference_area: float,
        low_speed_climb_polar: Polar,
        high_speed_polar: Polar,
        cruise_mach: float,
        thrust_rates: Dict[FlightPhase, float],
        time_step=None,
    ):
        """

        :param propulsion:
        :param reference_area:
        :param low_speed_climb_polar:
        :param high_speed_polar:
        :param cruise_mach:
        :param thrust_rates:
        :param cruise_distance: in meters
        :param time_step: if provided, this time step will be applied for all segments.
        """

        self.flight_phase_kwargs = {
            "propulsion": propulsion,
            "reference_area": reference_area,
            "time_step": time_step,
        }

        self.low_speed_climb_polar = low_speed_climb_polar
        self.high_speed_polar = high_speed_polar
        self.cruise_mach = cruise_mach
        self.thrust_rates = thrust_rates
        self.time_step = time_step

        kwargs = {
            "propulsion": propulsion,
            "reference_area": reference_area,
            "time_step": time_step,
        }

        initial_climb = InitialClimbPhase(**kwargs, polar=low_speed_climb_polar, thrust_rate=1.0)
        climb = ClimbPhase(
            **kwargs, polar=high_speed_polar, thrust_rate=thrust_rates[FlightPhase.CLIMB],
        )
        climb.maximum_mach = self.cruise_mach
        cruise = CruiseSegment(
            **kwargs,
            target=FlightPoint(),
            polar=high_speed_polar,
            engine_setting=EngineSetting.CRUISE,
        )
        descent = DescentPhase(
            **kwargs, polar=high_speed_polar, thrust_rate=thrust_rates[FlightPhase.DESCENT]
        )
        super().__init__(
            cruise_distance, [initial_climb, climb], cruise, [descent],
        )
