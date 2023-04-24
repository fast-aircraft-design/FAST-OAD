"""
Classes for computation of routes (i.e. assemblies of climb, cruise and descent phases).
"""
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

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import root_scalar

from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from .base import FlightSequence, IFlightPart
from .segments.base import AbstractFlightSegment
from .segments.registered.cruise import CruiseSegment


@dataclass
class RangedRoute(FlightSequence):
    """
    Computes a route so that it covers the specified ground distance.

    The computed route will be made of:
        - any number of climb phases
        - one cruise segment
        - any number of descent phases.

    """

    #: Any number of flight phases that will occur before cruise.
    climb_phases: List[FlightSequence] = MANDATORY_FIELD

    #: The cruise phase.
    cruise_segment: CruiseSegment = MANDATORY_FIELD

    #: Any number of flight phases that will occur after cruise.
    descent_phases: List[FlightSequence] = MANDATORY_FIELD

    #: Target ground distance for whole route
    flight_distance: float = MANDATORY_FIELD

    #: Accuracy on actual total ground distance for the solver. In meters
    distance_accuracy: float = 0.5e3

    #: If True, cruise distance will be adjusted to match :attr:`flight_distance`
    solve_distance: bool = True

    def __post_init__(self):
        super().__post_init__()
        self.extend(self._get_flight_sequence())

        # We will use this to keep data along root_scalar process (see _solve_cruise_distance() )
        self._flight_points = None

    @property
    def cruise_distance(self):
        """
        Ground distance to be covered during cruise, as set in target of :attr:`cruise_segment`.
        """
        return self.cruise_segment.target.ground_distance

    @cruise_distance.setter
    def cruise_distance(self, cruise_distance):
        self.cruise_segment.target.ground_distance = float(cruise_distance)
        self.cruise_segment.target.set_as_relative("ground_distance")

    @property
    def cruise_speed(self) -> Optional[Tuple[str, float]]:
        """
        Type (among `true_airspeed`, `equivalent_airspeed` and `mach`) and value of cruise speed.
        """
        climb_segments = []
        for phase in self.climb_phases:
            climb_segments += phase

        climb_segments.reverse()
        for segment in climb_segments:
            for speed_param in ["true_airspeed", "equivalent_airspeed", "mach"]:
                speed_value = getattr(segment.target, speed_param)
                if speed_value and speed_value != AbstractFlightSegment.CONSTANT_VALUE:
                    return speed_param, speed_value

        return None

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        # In very simple cases, climb and descent phases can have fixed
        # covered ground distance. In that case, cruise distance is easy to
        # obtain from flight_distance.
        # In other cases, cruise distance is obtained using a solver.
        climb_descent_distances = []
        for phase in self.climb_phases + self.descent_phases:
            climb_descent_distances.extend(self._get_ground_distances(phase))

        # Using the input target distance for cruise
        if not self.solve_distance:
            return super().compute_from(start)

        # Solving the needed cruise distance to get target flight distance
        if 0.0 in climb_descent_distances:
            return self._solve_cruise_distance(start)

        # climb and descent distances are provided, cruise distance can be obtained easily.
        self.cruise_distance = self.flight_distance - np.sum(climb_descent_distances)
        return super().compute_from(start)

    def _get_flight_sequence(self) -> List[IFlightPart]:
        # The preliminary climb segment of the cruise segment is set to the
        # last segment before cruise.
        cruise_climb = self.climb_phases[-1]
        while isinstance(cruise_climb, FlightSequence):
            cruise_climb = cruise_climb[-1]
        self.cruise_segment.climb_segment = cruise_climb

        return self.climb_phases + [self.cruise_segment] + self.descent_phases

    @classmethod
    def _get_ground_distances(cls, phase: FlightSequence) -> list:
        ground_distances = []
        for flight_part in phase:
            if isinstance(flight_part, AbstractFlightSegment):
                ground_distances.append(flight_part.target.ground_distance)
            else:
                ground_distances.extend(cls._get_ground_distances(flight_part))

        return ground_distances

    def _solve_cruise_distance(self, start: FlightPoint) -> pd.DataFrame:
        """
        Adjusts cruise distance through a solver to have whole route that
        matches provided flight distance.
        """

        root_scalar(
            self._compute_flight,
            args=(start,),
            x0=self.flight_distance * 0.5,
            x1=self.flight_distance * 0.25,
            xtol=self.distance_accuracy,
            method="secant",
        )

        return self._flight_points

    def _compute_flight(self, cruise_distance, start: FlightPoint):
        """
        Computes flight for provided cruise distance

        :param cruise_distance:
        :param start:
        :return: difference between computed distance and self.flight_distance
        """
        self.cruise_distance = cruise_distance
        self._flight_points = super().compute_from(start)
        obtained_distance = (
            self._flight_points.iloc[-1].ground_distance
            - self._flight_points.iloc[0].ground_distance
        )
        return self.flight_distance - obtained_distance
