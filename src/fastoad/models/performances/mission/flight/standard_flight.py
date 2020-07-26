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

from scipy.constants import foot, knot

from fastoad.base.flight_point import FlightPoint
from fastoad.constants import FlightPhase, EngineSetting
from fastoad.models.propulsion import IPropulsion
from .base import AbstractSimpleFlight
from ..base import IFlightPart, AbstractManualThrustFlightPhase
from ..polar import Polar
from ..segments.altitude_change import AltitudeChangeSegment
from ..segments.cruise import CruiseSegment
from ..segments.speed_change import SpeedChangeSegment


class InitialClimbPhase(AbstractManualThrustFlightPhase):
    """
    Preset for initial climb phase.

    - Climbs up to 400ft at constant EAS
    - Accelerates to EAS = 250kt at constant altitude
    - Climbs up to 1500ft at constant EAS
    """

    @property
    def flight_sequence(self) -> List[Union[IFlightPart, str]]:
        return [
            AltitudeChangeSegment(
                target=FlightPoint(equivalent_airspeed="constant", altitude=400.0 * foot),
                engine_setting=EngineSetting.TAKEOFF,
                **self.segment_kwargs,
            ),
            SpeedChangeSegment(
                target=FlightPoint(equivalent_airspeed=250.0 * knot),
                engine_setting=EngineSetting.TAKEOFF,
                **self.segment_kwargs,
            ),
            AltitudeChangeSegment(
                target=FlightPoint(equivalent_airspeed="constant", altitude=1500.0 * foot),
                engine_setting=EngineSetting.TAKEOFF,
                **self.segment_kwargs,
            ),
        ]


class ClimbPhase(AbstractManualThrustFlightPhase):
    """
    Preset for climb phase.

    - Climbs up to 10000ft at constant EAS
    - Accelerates to EAS = 300kt at constant altitude
    - Climbs up to target altitude at constant EAS
    """

    def __init__(self, **kwargs):
        """
        Uses keyword arguments as for :meth:`AbstractManualThrustFlightPhase` with
        these additional keywords:

        :param maximum_mach: Mach number that won't be exceeded during climb
        :param target_altitude: target altitude in meters, can be a float or
                                AltitudeChangeSegment.OPTIMAL_ALTITUDE to target
                                altitude with maximum lift/drag ratio
        """

        if "maximum_mach" in kwargs:
            self.maximum_mach = kwargs.pop("maximum_mach")
        self.target_altitude = kwargs.pop("target_altitude")
        super().__init__(**kwargs)

    @property
    def flight_sequence(self) -> List[Union[IFlightPart, str]]:
        self.segment_kwargs["engine_setting"] = EngineSetting.CLIMB

        return [
            AltitudeChangeSegment(
                target=FlightPoint(equivalent_airspeed="constant", altitude=10000.0 * foot),
                **self.segment_kwargs,
            ),
            SpeedChangeSegment(
                target=FlightPoint(equivalent_airspeed=300.0 * knot), **self.segment_kwargs,
            ),
            AltitudeChangeSegment(
                target=FlightPoint(equivalent_airspeed="constant", altitude=self.target_altitude),
                **self.segment_kwargs,
                maximum_mach=self.maximum_mach,
            ),
        ]


class DescentPhase(AbstractManualThrustFlightPhase):
    """
    Preset for descent phase.

    - Descends down to EAS = 300kt at constant Mach
    - Descends down to 10000ft at constant EAS
    - Decelerates to EAS = 250kt
    - Descends down to target altitude at constant EAS
    """

    def __init__(self, **kwargs):
        """
        Uses keyword arguments as for :meth:`AbstractManualThrustFlightPhase` with
        this additional keyword:

        :param target_altitude: target altitude in meters
        """

        self.target_altitude = kwargs.pop("target_altitude")
        super().__init__(**kwargs)

    @property
    def flight_sequence(self) -> List[Union[IFlightPart, str]]:
        self.segment_kwargs["engine_setting"] = EngineSetting.IDLE
        return [
            AltitudeChangeSegment(
                target=FlightPoint(equivalent_airspeed=300.0 * knot, mach="constant"),
                **self.segment_kwargs,
            ),
            AltitudeChangeSegment(
                target=FlightPoint(altitude=10000.0 * foot, equivalent_airspeed="constant"),
                **self.segment_kwargs,
            ),
            SpeedChangeSegment(
                target=FlightPoint(equivalent_airspeed=250.0 * knot), **self.segment_kwargs,
            ),
            AltitudeChangeSegment(
                target=FlightPoint(altitude=self.target_altitude, equivalent_airspeed="constant"),
                **self.segment_kwargs,
            ),
        ]


class StandardFlight(AbstractSimpleFlight):
    """
    Defines and computes a standard flight mission.

    The flight sequence is:
    - initial climb
    - climb
    - cruise at constant altitude
    - descent
    """

    def __init__(
        self,
        propulsion: IPropulsion,
        reference_area: float,
        low_speed_climb_polar: Polar,
        high_speed_polar: Polar,
        cruise_mach: float,
        thrust_rates: Dict[FlightPhase, float],
        cruise_distance: float = 0.0,
        climb_target_altitude: float = AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL,
        descent_target_altitude: float = 1500.0 * foot,
        time_step=None,
    ):
        """

        :param propulsion:
        :param reference_area:
        :param low_speed_climb_polar:
        :param high_speed_polar:
        :param cruise_mach:
        :param thrust_rates:
        :param cruise_distance:
        :param climb_target_altitude: (in m) altitude where cruise will begin. If value is
                                      AltitudeChangeSegment.OPTIMAL_ALTITUDE (default), climb will
                                      stop when maximum lift/drag ratio is achieved. Cruise will go
                                      on at the same altitude.
        :param descent_target_altitude: (in m) altitude where descent will end in meters
                                        Default is 457.2m (1500ft)
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
        self.climb_target_altitude = climb_target_altitude
        self.descent_target_altitude = descent_target_altitude
        self.time_step = time_step

        kwargs = {
            "propulsion": propulsion,
            "reference_area": reference_area,
            "time_step": time_step,
        }

        initial_climb = InitialClimbPhase(
            **kwargs,
            polar=low_speed_climb_polar,
            thrust_rate=1.0,
            name=FlightPhase.INITIAL_CLIMB.value,
        )
        climb = ClimbPhase(
            **kwargs,
            polar=high_speed_polar,
            thrust_rate=thrust_rates[FlightPhase.CLIMB],
            target_altitude=self.climb_target_altitude,
            maximum_mach=self.cruise_mach,
            name=FlightPhase.CLIMB.value,
        )
        cruise = CruiseSegment(
            **kwargs,
            target=FlightPoint(),
            polar=high_speed_polar,
            engine_setting=EngineSetting.CRUISE,
            name=FlightPhase.CRUISE.value,
        )
        descent = DescentPhase(
            **kwargs,
            polar=high_speed_polar,
            thrust_rate=thrust_rates[FlightPhase.DESCENT],
            target_altitude=self.descent_target_altitude,
            name=FlightPhase.DESCENT.value,
        )
        super().__init__(
            cruise_distance, [initial_climb, climb], cruise, [descent],
        )
