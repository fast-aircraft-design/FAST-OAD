"""Classes for simulating cruise segments."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.constants import foot, g

from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.util import get_closest_flight_level

from .altitude_change import AltitudeChangeSegment
from ..time_step_base import (
    AbstractLiftFromWeightSegment,
    AbstractRegulatedThrustSegment,
    AbstractTimeStepFlightSegment,
)

_LOGGER = logging.getLogger(__name__)  # Logger for this module

# Warn if there's an altitude discontinuity (tolerance accounts for fuel burn during climb)
ALTITUDE_TOLERANCE = 5.0  # meters


@dataclass
class CruiseSegment(AbstractRegulatedThrustSegment, AbstractLiftFromWeightSegment):
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
        if AbstractTimeStepFlightSegment.constant_value_name not in [
            self.target.true_airspeed,
            self.target.equivalent_airspeed,
        ]:
            self.target.mach = AbstractTimeStepFlightSegment.constant_value_name

    def get_distance_to_target(
        self, flight_points: list[FlightPoint], target: FlightPoint
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

    Important: The segment computes the optimal altitude at the start point and sets it
    immediately. If the previous segment ended at a different altitude, there will be an
    instantaneous altitude change (no climb segment). To avoid this "teleportation",
    Consider adding a climb segment with the keyword 'optimal_altitude' as target before
    optimal cruise.

    Note: Maximum altitude enforcement is done in compute_from_start_to_target and
    _compute_next_altitude rather than overriding _check_values, since _check_values
    only validates but does not modify flight point values.
    """

    #: Maximum allowed altitude in meters for the optimal cruise.
    #: When the optimal altitude exceeds this value, the aircraft will stay at this
    #: maximum altitude and `CL` will be reduced accordingly. If None, no meter-based
    #: altitude cap is applied (only maximum_flight_level applies).
    maximum_altitude: float | None = None

    #: The maximum allowed flight level (i.e. multiple of 100 feet).
    #: This sets an altitude cap at `maximum_flight_level * 100 ft`. When the optimal
    #: altitude exceeds this limit, the aircraft will stay at the capped altitude
    #: and `CL` will be reduced. Both this and maximum_altitude can be set; the
    #: most restrictive (lowest) cap will be applied.
    maximum_flight_level: float = 500.0

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        initial_altitude = start.altitude
        optimal_altitude = self._get_optimal_altitude(start.mass, start.mach)

        # Compute altitude cap from maximum_altitude and maximum_flight_level (converted to meters)
        altitude_cap = self._get_altitude_cap()

        # Start of optimal cruise should match either the cap or the optimal starting altitude
        if altitude_cap is not None and optimal_altitude > altitude_cap:
            start.altitude = altitude_cap
        else:
            start.altitude = optimal_altitude

        # Warn if there's an altitude discontinuity (tolerance accounts for fuel burn during climb)
        if (
            initial_altitude is not None
            and abs(start.altitude - initial_altitude) > ALTITUDE_TOLERANCE
        ):
            _LOGGER.warning(
                "Optimal cruise segment '%s' starting at altitude "
                "%.0fm to fly at optimum CL, but previous segment ended at %.0fm. "
                "This creates an instantaneous altitude change of %.0fm. Consider adding a climb "
                "segment with the keyword 'optimal_altitude' as target before optimal cruise to "
                "avoid altitude discontinuity.",
                self.name,
                start.altitude,
                initial_altitude,
                abs(start.altitude - initial_altitude),
            )

        self.complete_flight_point(start)
        return super().compute_from_start_to_target(start, target)

    def _compute_next_altitude(self, next_point: FlightPoint, previous_point: FlightPoint):
        optimal_altitude = self._get_optimal_altitude(
            next_point.mass, previous_point.mach, altitude_guess=previous_point.altitude
        )
        altitude_cap = self._get_altitude_cap()

        if (altitude_cap is not None) and (
            (optimal_altitude > altitude_cap) or (previous_point.altitude >= altitude_cap)
        ):
            next_point.altitude = altitude_cap
        else:
            next_point.altitude = optimal_altitude

    def _get_altitude_cap(
        self,
    ) -> float | None:
        altitude_caps = []
        if self.maximum_altitude is not None:
            altitude_caps.append(self.maximum_altitude)
        if self.maximum_flight_level is not None:
            altitude_caps.append(self.maximum_flight_level * 100.0 * foot)
        return min(altitude_caps) if altitude_caps else None


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
    will be preceded by a climb segment. The :attr:`climb_segment` is automatically populated
    when this segment is used inside a route; it only needs to be explicitly set if you want to
    modify the climb behavior or when using the class directly without a route.

    (Target ground distance will be achieved by the sum of ground distances
    covered during climb and cruise)

    In this case, climb will be done up to the IFR Flight Level (as multiple of 100 feet) that
    ensures minimum mass decrease, while being at most equal to :attr:`maximum_flight_level`.
    """

    #: The AltitudeChangeSegment that can be used if a preliminary climb is needed (its target
    #: will be ignored).
    #: Note: When this segment is used inside a route, the climb_segment is automatically
    #: populated. This attribute only needs to be explicitly set if you want to modify the
    #: climb segment behavior or when using the class directly without a route.
    climb_segment: AltitudeChangeSegment | None = None

    #: The maximum allowed flight level (i.e. multiple of 100 feet).
    maximum_flight_level: float = 500.0

    def compute_from_start_to_target(self, start: FlightPoint, target: FlightPoint) -> pd.DataFrame:
        if self.climb_segment is not None:
            attr_dict = {
                key: val
                for key, val in self.climb_segment.__dict__.items()
                if not key.startswith("_")
            }
            attr_dict["target"] = target
            attr_dict["name"] = self.name + ":prepended_climb"
            if self.maximum_CL is not None:
                attr_dict["maximum_CL"] = self.maximum_CL
            climb_segment = AltitudeChangeSegment(**attr_dict)
        else:
            climb_segment = None

        cruise_segment = CruiseSegment(
            target=deepcopy(target),  # deepcopy needed because altitude will be modified.
            propulsion=self.propulsion,
            reference_area=self.reference_area,
            polar=self.polar,
            name=self.name,
            engine_setting=self.engine_setting,
        )

        if self.target.altitude == AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL:
            if climb_segment is None:
                # When using mission files via RangedRoute, climb_segment is auto-populated.
                # If not provided and we reach here, just treat as normal cruise at current
                # altitude.
                _LOGGER.warning(
                    "Cruise segment '%s' has target altitude OPTIMAL_FLIGHT_LEVEL but no "
                    "climb_segment is provided. Will cruise at current altitude instead. Consider"
                    " inserting the cruise segment inside a route or provide a climb_segment.",
                    self.name if self.name is not None else "<unnamed>",
                )
                cruise_segment.target.altitude = None
                return super().compute_from_start_to_target(start, target)
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
                if self.maximum_CL is not None and self.is_next_flight_level_exceeding_maximum_cl(
                    cruise_altitude, start
                ):
                    break

                new_results = self._climb_to_altitude_and_cruise(
                    start, cruise_altitude, climb_segment, cruise_segment
                )
                mass_loss = start.mass - new_results.mass.iloc[-1]

                go_to_next_level = mass_loss < old_mass_loss
                if go_to_next_level:
                    results = new_results

        elif target.altitude is not None and isinstance(target.altitude, (int, float)):
            if climb_segment is None:
                # When using mission files via RangedRoute, climb_segment is auto-populated.
                # If not provided and we reach here, just treat as normal cruise at current
                # altitude.
                _LOGGER.warning(
                    "Cruise segment '%s' has a target altitude %.1f m but no "
                    "climb_segment is provided. Will cruise at current altitude instead. Consider"
                    " inserting the cruise segment inside a route or provide a climb_segment.",
                    self.name if self.name is not None else "<unnamed>",
                    float(target.altitude),
                )
                cruise_segment.target.altitude = None
                return super().compute_from_start_to_target(start, target)
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

    def is_next_flight_level_exceeding_maximum_cl(
        self, altitude_next_flight_level: float, flight_point: FlightPoint
    ) -> bool:
        """
        Returns true if the CL at the next flight level is higher than the maximum_CL

        :param altitude_next_flight_level: the altitude of the next flight level in m
        :param flight_point: the current flight point
        """

        actual_flight_point = deepcopy(flight_point)
        next_level_flight_point = FlightPoint()
        next_level_flight_point.altitude = altitude_next_flight_level
        next_level_flight_point.mach = actual_flight_point.mach
        next_level_flight_point.mass = actual_flight_point.mass

        self.complete_flight_point(next_level_flight_point)

        return bool(next_level_flight_point.CL > self.maximum_CL)  # noqa: SIM300 false positive


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

        :param start: the initial flight point, defined for `CL`, `CD`, `mass` and `true_airspeed`
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
