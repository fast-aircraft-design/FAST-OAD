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
from dataclasses import dataclass

from fastoad.model_base.flight_point import FlightPoint
from .polar import Polar


@dataclass
class AbstractPolarModifier(ABC):

    """ """

    @abstractmethod
    def modify_polar(self, polar: Polar, flightpoint: FlightPoint) -> Polar:

        """
        :param polar: an instance of Polar
        :param flightpoint: an intance of FlightPoint containg only floats
        :return: the modified polar for the flight point
        """


@dataclass
class LegacyPolar(AbstractPolarModifier):
    def modify_polar(self, polar: Polar, flightpoint: FlightPoint) -> Polar:
        return polar


@dataclass
class GroundEffectRaymer(AbstractPolarModifier):

    """
    Evaluates the drag in ground effect, using Raymer's model:
        'Aircraft Design A conceptual approach', D. Raymer p304
    """

    # The wingspan
    span: float

    # The main landing gear height
    landing_gear_height: float

    # The induced drag coefficient, multiplies CL**2 to obtain the induced drag
    induced_drag_coef: float

    # The winglet effect tuning coefficient
    k_winglet: float

    # The total drag tuning coefficient
    k_cd: float

    def modify_polar(self, polar: Polar, flightpoint: FlightPoint) -> Polar:

        h_b = (self.span * 0.1 + self.landing_gear_height + flightpoint.altitude) / self.span
        k_ground = 33.0 * h_b ** 1.5 / (1 + 33.0 * h_b ** 1.5)
        cd_ground = (
            self.induced_drag_coef
            * polar.definition_cl ** 2
            * self.k_winglet
            * self.k_cd
            * (k_ground - 1)
        )

        # Update polar interpolation
        modified_polar = Polar(
            polar.definition_cl,
            polar.definition_cd + cd_ground,
            cl_alpha=polar.CL_alpha,
            cl0_clean=polar.CL_alpha_0,
            cl_high_lift=polar.CL_high_lift,
        )

        return modified_polar
