"""Aerodynamics polar modifier."""
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
    """Base class to implement a change to the aerodynamic polar during mission computation.

    A polar modifier is applied to the segment's polar at each computation step,
    allowing dynamic modification of drag (e.g. ground effect) based on flight conditions.

    Subclasses must implement :meth:`modify_polar` and be registered using
    :class:`RegisterPolarModifier` to be usable in a mission definition file.
    """

    @abstractmethod
    def modify_polar(self, polar: Polar, flight_point: FlightPoint) -> Polar:
        """Apply a modification to the polar for a given flight point.

        :param polar: the original polar instance (unitless CL/CD)
        :param flight_point: a FlightPoint instance containing the flight conditions
            (altitude, speed, etc.) as floats
        :return: a new Polar instance with the modification applied
        """


class RegisterPolarModifier(RegisterElement, base_class=AbstractPolarModifier):
    """Decorator for registering an AbstractPolarModifier subclass for use in mission files.

    The keyword provided to the decorator is used as the ``name`` value in the
    ``modifier`` sub-key of the ``polar`` parameter in a mission definition file.

    Usage example::

        @RegisterPolarModifier("ground_effect_raymer")
        @dataclass
        class MyPolarModifier(AbstractPolarModifier):
            ...

    The registered class can then be retrieved using
    :meth:`RegisterPolarModifier.get_class`.

    In a mission definition file, the registered modifier is used as follows:

    .. code-block:: yaml

        polar:
          CL: data:aerodynamics:aircraft:takeoff:CL
          CD: data:aerodynamics:aircraft:takeoff:CD
          modifier:
            name: ground_effect_raymer
            ...
    """


@RegisterPolarModifier("none")
@dataclass
class UnchangedPolar(AbstractPolarModifier):
    """Default polar modifier that returns the polar unchanged.

    This modifier applies no transformation and is equivalent to not specifying
    a modifier at all.
    """

    def modify_polar(self, polar: Polar, flight_point: FlightPoint) -> Polar:
        """Return the polar unchanged.

        :param polar: a Polar instance
        :param flight_point: a FlightPoint instance
        :return: the same polar instance
        """
        return polar


@RegisterPolarModifier("ground_effect_raymer")
@dataclass
class GroundEffectRaymer(AbstractPolarModifier):
    """Evaluates the drag reduction due to ground effect using Raymer's model.

    Reference: *Aircraft Design: A Conceptual Approach*, D. Raymer, p. 304.

    The ground effect is computed from the altitude of the flight point relative
    to the ground, the wingspan, and the main landing gear height. The induced
    drag is decreased by a factor that depends on the proximity to the ground:
    the correction term (k_ground - 1) is negative, hence the drag coefficient
    of the polar is reduced.

    :param span: wingspan (m)
    :param landing_gear_height: main landing gear height (m)
    :param induced_drag_coefficient: coefficient multiplying CL**2 for induced drag
        (unitless)
    :param k_winglet: winglet effect tuning coefficient (unitless)
    :param k_cd: total drag tuning coefficient (unitless)
    :param ground_altitude: altitude of ground w.r.t. sea level (m), default 0.0
    """

    #: Wingspan (m)
    span: float

    #: Main landing gear height (m)
    landing_gear_height: float

    #: Induced drag coefficient (unitless), multiplies CL**2 to obtain the induced drag
    induced_drag_coefficient: float

    #: Winglet effect tuning coefficient (unitless)
    k_winglet: float

    #: Total drag tuning coefficient (unitless)
    k_cd: float

    #: Altitude of ground w.r.t. sea level (m)
    ground_altitude: float = 0.0

    def modify_polar(self, polar: Polar, flight_point: FlightPoint) -> Polar:
        """Compute the ground effect correction and return a modified polar.

        :param polar: the original Polar instance to modify
        :param flight_point: a FlightPoint instance containing the flight conditions
            (altitude (m), speed, etc.) for ground effect calculation
        :return: a new Polar instance, with the ground effect correction applied to
            the drag coefficient
        """

        h_b = (
            abs(
                self.span * 0.1
                + self.landing_gear_height
                + flight_point.altitude
                - self.ground_altitude
            )
            / self.span
        )
        k_ground = 33.0 * h_b**1.5 / (1 + 33.0 * h_b**1.5)
        cd_ground = (
            self.induced_drag_coefficient
            * polar.definition_cl**2
            * self.k_winglet
            * self.k_cd
            * (k_ground - 1)
        )

        # Update polar interpolation
        return Polar(  # modified_polar
            polar.definition_cl,
            polar.definition_cd + cd_ground,
            polar.definition_alpha,
        )
