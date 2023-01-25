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

from abc import ABC, abstractmethod

from fastoad.model_base.flight_point import FlightPoint
from .polar import Polar


class AbstractPolarModifier(ABC):

    """ """

    @abstractmethod
    def ModifyPolar(self, polar: Polar, flightpoint: FlightPoint) -> Polar:

        """
        :param polar: an instance of Polar
        :param flightpoint: an intance of FlightPoint containg only floats
        :return: the modified polar for the flight point
        """


class LegacyPolar(AbstractPolarModifier):
    def ModifyPolar(self, polar: Polar, flightpoint: FlightPoint) -> Polar:
        return polar


class GroundEffectRaymer(AbstractPolarModifier):

    """
    Evaluates the drag in ground effect, using Raymer's model:
        'Aircraft Design A conceptual approach', D. Raymer p304
    """

    def __init__(self, span, lg_height, induced_drag_coef, k_winglet, k_cd):

        self._span = span
        self._lg_height = lg_height
        self._induced_drag_coef = induced_drag_coef
        self._k_winglet = k_winglet
        self._k_cd = k_cd

    def ModifyPolar(self, polar: Polar, flightpoint: FlightPoint) -> Polar:

        h_b = (self._span * 0.1 + self._lg_height + flightpoint.altitude) / self._span
        k_ground = 33.0 * h_b ** 1.5 / (1 + 33.0 * h_b ** 1.5)
        cd_ground = (
            self._induced_drag_coef
            * polar.definition_cl ** 2
            * self._k_winglet
            * self._k_cd
            * (k_ground - 1)
        )

        # Update polar interpolation
        polar.interpolate_cd(polar.definition_cl, polar.definition_cd + cd_ground)

        return polar
