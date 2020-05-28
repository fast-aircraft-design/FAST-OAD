"""
Base module for engine models
"""

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

from abc import ABC, abstractmethod
from typing import Union, Sequence, Optional, Tuple

import numpy as np
import openmdao.api as om
from fastoad.constants import FlightPhase
from numpy import linspace


class IEngine(ABC):
    """
    Interface for Engine models
    """

    # pylint: disable=too-few-public-methods  # that is the needed interface

    # pylint: disable=too-many-arguments  # they define the trajectory
    @abstractmethod
    def compute_flight_points(
        self,
        mach: Union[float, Sequence],
        altitude: Union[float, Sequence],
        phase: Union[FlightPhase, Sequence],
        use_thrust_rate: Optional[Union[bool, Sequence]] = None,
        thrust_rate: Optional[Union[float, Sequence]] = None,
        thrust: Optional[Union[float, Sequence]] = None,
    ) -> Tuple[Union[float, Sequence], Union[float, Sequence], Union[float, Sequence]]:
        """
        Computes Specific Fuel Consumption according to provided conditions.

        Each input can be a float, a list or an array.
        Inputs that are not floats must all have the same shape (numpy speaking).

        About use_thrust_rate, thrust_rate and thrust
        ---------------------------------------------

            *use_thrust_rate* tells if a flight point should be computed using *thrust_rate*
            or *thrust* as input.

            - if *use_thrust_rate* is None, the considered input will be the provided one
            between *thrust_rate* and *thrust* (if both are provided, *thrust_rate* will be used)

            - if *use_thrust_rate* is True or False (i.e., not a sequence), the considered input
            will be taken accordingly, and should of course not be None.

            - if *use_thrust_rate* is a sequence or array, *thrust_rate* and *thrust* should be
            provided and have the same shape as *use_thrust_rate*. The method will consider for
            each element which input will be used according to *use_thrust_rate*


        :param mach: Mach number
        :param altitude: (unit=m) altitude w.r.t. to sea level
        :param phase: flight phase
        :param use_thrust_rate: tells if thrust_rate or thrust should be used (works element-wise)
        :param thrust_rate: thrust rate (unit=none)
        :param thrust: required thrust (unit=N)
        :return: SFC (in kg/s/N), thrust rate, thrust (in N)
        """


class OMIEngine(om.ExplicitComponent, ABC):
    """
    Base class for OpenMDAO wrapping of subclasses of :class`IEngine`.

    Classes that implements this interface should add their own inputs in setup()
    and implement :meth:`get_engine`.
    """

    def initialize(self):
        self.options.declare("flight_point_count", 1, types=(int, tuple))

    def setup(self):
        shape = self.options["flight_point_count"]
        self.add_input("data:propulsion:mach", np.nan, shape=shape)
        self.add_input("data:propulsion:altitude", np.nan, shape=shape, units="m")
        self.add_input("data:propulsion:phase", np.nan, shape=shape)
        self.add_input("data:propulsion:use_thrust_rate", np.nan, shape=shape)
        self.add_input("data:propulsion:required_thrust_rate", np.nan, shape=shape)
        self.add_input("data:propulsion:required_thrust", np.nan, shape=shape, units="N")

        self.add_output("data:propulsion:SFC", shape=shape, units="kg/s/N", ref=1e-4)
        self.add_output("data:propulsion:thrust_rate", shape=shape, lower=0.0, upper=1.0)
        self.add_output("data:propulsion:thrust", shape=shape, units="N", ref=1e5)

        self.declare_partials("data:propulsion:SFC", "*", method="fd")
        self.declare_partials("data:propulsion:thrust_rate", "*", method="fd")
        self.declare_partials("data:propulsion:thrust", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        engine = self.get_engine(inputs)
        sfc, thrust_rate, thrust = engine.compute_flight_points(
            inputs["data:propulsion:mach"],
            inputs["data:propulsion:altitude"],
            inputs["data:propulsion:phase"],
            inputs["data:propulsion:use_thrust_rate"],
            inputs["data:propulsion:required_thrust_rate"],
            inputs["data:propulsion:required_thrust"],
        )
        outputs["data:propulsion:SFC"] = sfc
        outputs["data:propulsion:thrust_rate"] = thrust_rate
        outputs["data:propulsion:thrust"] = thrust

    @staticmethod
    @abstractmethod
    def get_engine(inputs) -> IEngine:
        """

        :param inputs: input parameters that define the engine
        :return: a :class`IEngineSubclass` instance
        """


class EngineTable(om.ExplicitComponent, ABC):
    """
    This class computes engine tables, that is to say 2 4D tables:

        Specific Fuel Consumption = f(Mach, altitude, thrust rate, flight phase)
        thrust = f(Mach, altitude, thrust rate, flight phase)
    """

    def setup(self):
        self.options.declare(
            "mach_min", default=0.0, types=float, desc="Minimum value Mach number ",
        )
        self.options.declare(
            "mach_max", default=1.0, types=float, desc="Maximum value for Mach number ",
        )
        self.options.declare(
            "mach_step_count", default=100, types=int, desc="Step count for Mach number",
        )
        self.options.declare(
            "altitude_min", default=0.0, types=float, desc="Minimum value for altitude in meters",
        )
        self.options.declare(
            "altitude_max",
            default=13500.0,
            types=float,
            desc="Maximum value for altitude in meters",
        )
        self.options.declare(
            "altitude_step_count", default=100, types=int, desc="Step count for thrust rate",
        )

        self.options.declare(
            "thrust_rate_min", default=0.0, types=float, desc="Minimum value for thrust rate",
        )
        self.options.declare(
            "thrust_rate_max", default=1.0, types=float, desc="Maximum value for thrust rate",
        )
        self.options.declare(
            "thrust_rate_step_count", default=20, types=int, desc="Step count for thrust rate",
        )

        self.options.declare("flight_phases", default=[phase for phase in FlightPhase], types=list)

        shape = self._get_shape()
        self.add_output("private:propulsion:table:mach", shape=shape[0])
        self.add_output("private:propulsion:table:altitude", shape=shape[1], units="m")
        self.add_output("private:propulsion:table:thrust_rate", shape=shape[2])
        self.add_output("private:propulsion:table:flight_phase", shape=shape[3])
        self.add_output("private:propulsion:table:SFC", shape=shape, units="kg/s/N")
        self.add_output("private:propulsion:table:thrust", shape=shape, units="N")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        for var in ["mach", "altitude", "thrust_rate"]:
            outputs["private:propulsion:table:%s" % var] = linspace(
                self.options["%s_min" % var],
                self.options["%s_max" % var],
                self.options["%s_step_count" % var] + 1,
            )

        outputs["private:propulsion:table:flight_phase"] = [
            int(phase) for phase in self.options["flight_phases"]
        ]

        mach = outputs["private:propulsion:table:mach"][:, None, None, None]
        altitude = outputs["private:propulsion:table:altitude"][None, :, None, None]
        thrust_rate = outputs["private:propulsion:table:thrust_rate"][None, None, :, None]
        phase = outputs["private:propulsion:table:flight_phase"][None, None, None, :]

        shape = self._get_shape()

        mach = np.tile(mach, (1, *shape[1:]))
        altitude = np.tile(altitude, (shape[0], 1, *shape[2:]))
        thrust_rate = np.tile(thrust_rate, (*shape[:2], 1, shape[3]))
        phase = np.tile(phase, (*shape[:3], 1))

        SFC, _, thrust = self.get_engine(inputs).compute_flight_points(
            mach, altitude, phase, thrust_rate=thrust_rate,
        )

        outputs["private:propulsion:table:SFC"] = SFC
        outputs["private:propulsion:table:thrust"] = thrust

    def _get_shape(self):
        nb_mach_values = self.options["mach_step_count"] + 1
        nb_altitude_values = self.options["altitude_step_count"] + 1
        nb_thrust_rate_values = self.options["thrust_rate_step_count"] + 1
        nb_flight_phases = len(self.options["flight_phases"])

        return (
            nb_mach_values,
            nb_altitude_values,
            nb_thrust_rate_values,
            nb_flight_phases,
        )

    @staticmethod
    @abstractmethod
    def get_engine(inputs) -> IEngine:
        """

        :param inputs: input parameters that define the engine
        :return: a :class`IEngineSubclass` instance
        """
