"""
Classes for computation of routes (i.e. assemblies of climb, cruise and descent phases).
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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
from fastoad.models.performances.mission.base import FlightSequence, IFlightPart
from fastoad.models.performances.mission.segments.base import FlightSegment
from fastoad.models.performances.mission.segments.cruise import CruiseSegment


@dataclass
class SimpleRoute(FlightSequence):
    """
    Computes a simple route.

    The computed route will be be made of:
        - any number of climb phases
        - one cruise segment
        - any number of descent phases.
    """

    #: Any number of flight phases that will occur before cruise.
    climb_phases: List[FlightSequence]

    #: The cruise phase.
    cruise_segment: CruiseSegment

    #: Any number of flight phases that will occur after cruise.
    descent_phases: List[FlightSequence]

    def __post_init__(self):
        super().__post_init__()
        self.flight_sequence.extend(self._get_flight_sequence())

    @property
    def cruise_distance(self):
        """
        Ground distance to be covered during cruise, as set in target of :attr:`cruise_segment`.
        """
        return self.cruise_segment.target

    @cruise_distance.setter
    def cruise_distance(self, cruise_distance):
        self.cruise_segment.target.ground_distance = cruise_distance

    @property
    def cruise_speed(self) -> Optional[Tuple[str, float]]:
        """
        Type (among `true_airspeed`, `equivalent_airspeed` and `mach`) and value of cruise speed.
        """
        climb_segments = []
        for phase in self.climb_phases:
            climb_segments += phase.flight_sequence

        climb_segments.reverse()
        for segment in climb_segments:
            for speed_param in ["true_airspeed", "equivalent_airspeed", "mach"]:
                speed_value = getattr(segment.target, speed_param)
                if speed_value and speed_value != FlightSegment.CONSTANT_VALUE:
                    return speed_param, speed_value

        return None

    def _get_flight_sequence(self) -> List[IFlightPart]:
        # The preliminary climb segment of the cruise segment is set to the
        # last segment before cruise.
        cruise_climb = self.climb_phases[-1]
        while isinstance(cruise_climb, FlightSequence):
            cruise_climb = cruise_climb.flight_sequence[-1]
        self.cruise_segment.climb_segment = cruise_climb

        return self.climb_phases + [self.cruise_segment] + self.descent_phases


@dataclass
class RangedRoute(SimpleRoute):
    """
    Computes a route so that it covers the specified ground distance.
    """

    #: Target ground distance for whole route
    flight_distance: float

    #: Accuracy on actual total ground distance for the solver. In meters
    distance_accuracy: float = 0.5e3

    def __post_init__(self):
        super().__post_init__()

        # We will use this to keep data along root_scalar process (see _solve_cruise_distance() )
        self._flight_points = None

    def compute_from(self, start: FlightPoint) -> pd.DataFrame:
        # In very simple cases, climb and descent phases can have fixed
        # covered ground distance. In that case, cruise distance is easy to
        # obtain from flight_distance.
        # In other cases, cruise distance is obtained using a solver.
        climb_descent_distances = []
        for phase in self.climb_phases + self.descent_phases:
            climb_descent_distances.extend(self._get_ground_distances(phase))

        if 0.0 in climb_descent_distances:
            return self._solve_cruise_distance(start)

        self.cruise_distance = self.flight_distance - np.sum(climb_descent_distances)
        return super().compute_from(start)

    @classmethod
    def _get_ground_distances(cls, phase: FlightSequence) -> list:
        ground_distances = []
        for flight_part in phase.flight_sequence:
            if isinstance(flight_part, FlightSegment):
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
            xtol=0.5e3,
            method="secant",
        )

        return self._flight_points

    def _compute_flight(self, cruise_distance, start: FlightPoint):
        """
        Computes flight for provided cruise distance

        :param cruise_distance:
        :param start:
        :return: difference between computes distance and self.flight_distance
        """
        self.cruise_distance = cruise_distance
        self._flight_points = super().compute_from(start)
        obtained_distance = (
            self._flight_points.iloc[-1].ground_distance
            - self._flight_points.iloc[0].ground_distance
        )
        return self.flight_distance - obtained_distance
