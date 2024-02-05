"""Classes for simulating cruise segments."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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

from copy import deepcopy
from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd
from scipy.constants import foot, g

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.util import get_closest_flight_level
from .altitude_change import AltitudeChangeSegment
from ..time_step_base import AbstractRegulatedThrustSegment, AbstractTimeStepFlightSegment


@dataclass
class CruiseSegment(AbstractRegulatedThrustSegment):
    """
    Class for computing cruise flight segment at constant altitude and speed.

    Mach is considered constant, equal to Mach at starting point.
    Altitude is constant.
    Target is a specified ground_distance. The target definition indicates
    the ground_distance to be covered during the segment, independently of
    the initial value.
    """

    def __post_init__(self):
        super().__post_init__()
        # Constant speed at constant altitude is necessarily constant Mach, but
        # subclasses can be at variable altitude, so Mach is considered constant
        # if no other constant speed parameter is set to "constant".
        if AbstractTimeStepFlightSegment.CONSTANT_VALUE not in [
            self.target.true_airspeed,
            self.target.equivalent_airspeed,
        ]:
            self.target.mach = AbstractTimeStepFlightSegment.CONSTANT_VALUE

    def get_distance_to_target(
        self, flight_points: List[FlightPoint], target: FlightPoint
    ) -> float:
        current = flight_points[-1]
        return target.ground_distance - current.ground_distance


@RegisterSegment("optimal_cruise")
@dataclass
class OptimalCruiseSegment(CruiseSegment):
    """
    Class for computing cruise flight segment at maximum lift/drag ratio.

    Altitude is set **at every point** to get the optimum CL according to current mass.
    Target is a specified ground_distance. The target definition indicates
    the ground_distance to be covered during the segment, independently of
    the initial value.
    Target should also specify a speed parameter set to "constant", among `mach`,
    `true_airspeed` and `equivalent_airspeed`. If not, Mach will be assumed constant.
    """

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        start.altitude = self._get_optimal_altitude(start.mass, start.mach)
        self.complete_flight_point(start)
        return super().compute_from_start_to_target(start, target)

    def _compute_next_altitude(self, next_point: FlightPoint, previous_point: FlightPoint):
        next_point.altitude = self._get_optimal_altitude(
            next_point.mass, previous_point.mach, altitude_guess=previous_point.altitude
        )


@RegisterSegment("cruise")
@dataclass
class ClimbAndCruiseSegment(CruiseSegment):
    """
    Class for computing cruise flight segment at constant altitude.

    Target is a specified ground_distance. The target definition indicates
    the ground_distance to be covered during the segment, independently of
    the initial value.
    Target should also specify a speed parameter set to "constant", among `mach`,
    `true_airspeed` and `equivalent_airspeed`. If not, Mach will be assumed constant.

    Target altitude can also be set to
    :attr:`~.altitude_change.AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL`. In that case, the cruise
    will be preceded by a climb segment and :attr:`climb_segment` must be set at instantiation.

    (Target ground distance will be achieved by the sum of ground distances
    covered during climb and cruise)

    In this case, climb will be done up to the IFR Flight Level (as multiple of 100 feet) that
    ensures minimum mass decrease, while being at most equal to :attr:`maximum_flight_level`.
    """

    #: The AltitudeChangeSegment that can be used if a preliminary climb is needed (its target
    #: will be ignored).
    climb_segment: AltitudeChangeSegment = None

    #: The maximum allowed flight level (i.e. multiple of 100 feet).
    maximum_flight_level: float = 500.0

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        climb_segment = deepcopy(self.climb_segment)
        climb_segment.target = target

        cruise_segment = CruiseSegment(
            target=deepcopy(target),  # deepcopy needed because altitude will be modified.
            propulsion=self.propulsion,
            reference_area=self.reference_area,
            polar=self.polar,
            name=self.name,
            engine_setting=self.engine_setting,
        )

        if (
            self.target.altitude == AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL
            and climb_segment is not None
        ):
            cruise_segment.target.altitude = None

            # Go to the next flight level, or keep altitude if already at a flight level
            cruise_altitude = get_closest_flight_level(start.altitude - 1.0e-3)
            results = self._climb_to_altitude_and_cruise(
                start, cruise_altitude, climb_segment, cruise_segment
            )
            mass_loss = start.mass - results.mass.iloc[-1]

            go_to_next_level = True

            while go_to_next_level:
                old_mass_loss = mass_loss
                cruise_altitude = get_closest_flight_level(cruise_altitude + 1.0e-3)
                if cruise_altitude > self.maximum_flight_level * 100.0 * foot:
                    break

                new_results = self._climb_to_altitude_and_cruise(
                    start, cruise_altitude, climb_segment, cruise_segment
                )
                mass_loss = start.mass - new_results.mass.iloc[-1]

                go_to_next_level = mass_loss < old_mass_loss
                if go_to_next_level:
                    results = new_results

        elif target.altitude is not None:
            results = self._climb_to_altitude_and_cruise(
                start, target.altitude, climb_segment, cruise_segment
            )
        else:
            results = super().compute_from_start_to_target(start, target)

        return results

    @staticmethod
    def _climb_to_altitude_and_cruise(
        start: FlightPoint,
        cruise_altitude: float,
        climb_segment: AltitudeChangeSegment,
        cruise_segment: CruiseSegment,
    ):
        """
        Climbs up to cruise_altitude and cruise, while ensuring final ground_distance is
        equal to self.target.ground_distance.

        :param start:
        :param cruise_altitude:
        :param climb_segment:
        :param cruise_segment:
        :return:
        """
        climb_segment.target = FlightPoint(
            altitude=cruise_altitude,
            mach=cruise_segment.target.mach,
            true_airspeed=cruise_segment.target.true_airspeed,
            equivalent_airspeed=cruise_segment.target.equivalent_airspeed,
        )
        climb_points = climb_segment.compute_from(start)

        cruise_start = FlightPoint.create(climb_points.iloc[-1])
        cruise_points = cruise_segment.compute_from(cruise_start)

        return pd.concat([climb_points, cruise_points]).reset_index(drop=True)


@RegisterSegment("breguet")
@dataclass
class BreguetCruiseSegment(CruiseSegment):
    """
    Class for computing cruise flight segment at constant altitude using Breguet-Leduc formula.

    As formula relies on SFC, the :attr:`propulsion` model must be able to fill FlightPoint.sfc
    when FlightPoint.thrust is provided.
    """

    #: if True, max lift/drag ratio will be used instead of the one computed with polar using
    #: CL deduced from mass and altitude.
    #: In this case, reference_area parameter will be unused
    use_max_lift_drag_ratio: bool = False

    #: The reference area, in m**2. Used only if use_max_lift_drag_ratio is False.
    reference_area: float = 1.0

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        cruise_mass_ratio = self._compute_cruise_mass_ratio(
            start, target.ground_distance - start.ground_distance
        )

        end = deepcopy(start)
        self.consume_fuel(end, previous=start, mass_ratio=cruise_mass_ratio)
        end.ground_distance = target.ground_distance
        end.time = start.time + (end.ground_distance - start.ground_distance) / end.true_airspeed
        end.name = self.name
        self.complete_flight_point(end)

        return pd.DataFrame([start, end])

    def _compute_cruise_mass_ratio(self, start: FlightPoint, cruise_distance):
        """
        Computes mass ratio between end and start of cruise

        :param start: the initial flight point, defined for `CL`, `CD`, `mass` and`true_airspeed`
        :param cruise_distance: cruise distance in meters
        :return: (mass at end of cruise) / (mass at start of cruise)
        """

        if self.use_max_lift_drag_ratio:
            lift_drag_ratio = self.polar.optimal_cl / self.polar.cd(self.polar.optimal_cl)
        else:
            lift_drag_ratio = start.CL / start.CD
        start.thrust = start.mass / lift_drag_ratio * g
        self.propulsion.compute_flight_points(start)

        range_factor = start.true_airspeed * lift_drag_ratio / g / start.sfc
        return 1.0 / np.exp(cruise_distance / range_factor)
