""" Aerodynamics polar modifier."""
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

from abc import ABC, abstractmethod
from dataclasses import dataclass

from fastoad.model_base.flight_point import FlightPoint
from .base import RegisterElement
from .polar import Polar


@dataclass
class AbstractPolarModifier(ABC):

    """
    Base class to implement a change to the polar during the mission computation
    """

    @abstractmethod
    def modify_polar(self, polar: Polar, flight_point: FlightPoint) -> Polar:

        """
        :param polar: an instance of Polar
        :param flight_point: an intance of FlightPoint containg only floats
        :return: the modified polar for the flight point
        """


class RegisterPolarModifier(RegisterElement, base_class=AbstractPolarModifier):
    """
    Decorator for registering AbstractPolarModifier classes.

        >>> @RegisterPolarModifier("polar_modifier_foo")
        >>> class FooPolarModifier(IFlightPart):
        >>>     ...

    Then the registered class can be obtained by:

        >>> my_class = RegisterPolarModifier.get_class("polar_modifier_foo")
    """


@RegisterPolarModifier("none")
@dataclass
class UnchangedPolar(AbstractPolarModifier):
    """
    Default polar modifier returning the polar without changes
    """

    def modify_polar(self, polar: Polar, flight_point: FlightPoint) -> Polar:
        """
        :param polar: a polar instance
        :param flight_point: a FlightPoint instance
        :return: the polar instance
        """
        return polar


@RegisterPolarModifier("ground_effect_raymer")
@dataclass
class GroundEffectRaymer(AbstractPolarModifier):

    """
    Evaluates the drag in ground effect, using Raymer's model:
        'Aircraft Design A conceptual approach', D. Raymer p304
    """

    #: Wingspan
    span: float

    #: Main landing gear height
    landing_gear_height: float

    #: Induced drag coefficient, multiplies CL**2 to obtain the induced drag
    induced_drag_coefficient: float

    #: Winglet effect tuning coefficient
    k_winglet: float

    #: Total drag tuning coefficient
    k_cd: float

    #: Altitude of ground w.r.t. sea level
    ground_altitude: float = 0.0

    def modify_polar(self, polar: Polar, flight_point: FlightPoint) -> Polar:
        """
        Compute the ground effect based on altitude from ground and return an updated polar

        :param polar: a Polar instance used as basis to apply ground effect
        :param flight_point: a flight point containing the flight conditions
        for calculation of ground effect
        :return: a copy of polar with ground effect
        """

        h_b = (
            self.span * 0.1
            + self.landing_gear_height
            + flight_point.altitude
            - self.ground_altitude
        ) / self.span
        k_ground = 33.0 * h_b ** 1.5 / (1 + 33.0 * h_b ** 1.5)
        cd_ground = (
            self.induced_drag_coefficient
            * polar.definition_cl ** 2
            * self.k_winglet
            * self.k_cd
            * (k_ground - 1)
        )

        # Update polar interpolation
        modified_polar = Polar(
            polar.definition_cl,
            polar.definition_cd + cd_ground,
            polar.definition_alpha,
        )

        return modified_polar
