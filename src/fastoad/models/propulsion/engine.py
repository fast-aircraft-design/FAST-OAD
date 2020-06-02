"""Base module for engine models."""

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
from typing import Union, Sequence, Optional, Tuple, Mapping

import numpy as np
import openmdao.api as om
from fastoad.constants import FlightPhase
from numpy import linspace
from openmdao.core.component import Component
from scipy.interpolate import RegularGridInterpolator


class IEngine(ABC):
    """
    Interface for Engine models.
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
        This method defines the IEngine-derived instance used by the OpenMDAO component.

        :param inputs: input parameters that define the engine
        :return: the engine instance
        """


class EngineTable(om.ExplicitComponent, ABC):
    """
    This class computes engine tables.

    Engine tables are two 4D tables:

        Specific Fuel Consumption = f(Mach, altitude, thrust rate, flight phase)
        thrust = f(Mach, altitude, thrust rate, flight phase)
    """

    MACH_MIN = 0.0
    MACH_MAX = 1.0
    MACH_STEP_COUNT = 100
    ALTITUDE_MIN = 0.0
    ALTITUDE_MAX = 13500.0
    ALTITUDE_STEP_COUNT = 100
    THRUST_RATE_MIN = 0.0
    THRUST_RATE_MAX = 1.0
    THRUST_RATE_STEP_COUNT = 20
    FLIGHT_PHASES = FlightPhase  # The enum class acts as a list of its values

    def setup(self):
        shape = self._get_shape()
        self.add_output("private:propulsion:table:mach", shape=shape[0])
        self.add_output("private:propulsion:table:altitude", shape=shape[1], units="m")
        self.add_output("private:propulsion:table:thrust_rate", shape=shape[2])
        self.add_output("private:propulsion:table:flight_phase", shape=shape[3])
        self.add_output("private:propulsion:table:SFC", shape=shape, units="kg/s/N")
        self.add_output("private:propulsion:table:thrust", shape=shape, units="N")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        outputs["private:propulsion:table:mach"] = linspace(
            self.MACH_MIN, self.MACH_MAX, self.MACH_STEP_COUNT + 1
        )
        outputs["private:propulsion:table:altitude"] = linspace(
            self.ALTITUDE_MIN, self.ALTITUDE_MAX, self.ALTITUDE_STEP_COUNT + 1
        )
        outputs["private:propulsion:table:thrust_rate"] = linspace(
            self.THRUST_RATE_MIN, self.THRUST_RATE_MAX, self.THRUST_RATE_STEP_COUNT + 1
        )
        outputs["private:propulsion:table:flight_phase"] = [
            int(phase) for phase in self.FLIGHT_PHASES
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

    @classmethod
    def _get_shape(cls):
        return (
            cls.MACH_STEP_COUNT + 1,
            cls.ALTITUDE_STEP_COUNT + 1,
            cls.THRUST_RATE_STEP_COUNT + 1,
            len(cls.FLIGHT_PHASES),
        )

    @staticmethod
    @abstractmethod
    def get_engine(inputs) -> IEngine:
        """
        This method defines the engine instance used for generating the table.

        :param inputs: input parameters that define the engine
        :return: a :class`IEngineSubclass` instance
        """

    @classmethod
    def interpolate_SFC(
        cls,
        inputs: Mapping,
        mach: Union[float, Sequence[float]],
        altitude: Union[float, Sequence[float]],
        thrust_rate: Union[float, Sequence[float]],
        flight_phase: Union[FlightPhase, Sequence[FlightPhase]],
    ):
        """
        Convenience method for interpolating in SFC table provided by :meth:`compute`.

        Note: `mach`, `altitude`, `thrust_rate` and `flight_phase` must have the same size.

        :param inputs: a dict-like that provides OpenMDAO outputs from self.compute()
        :param mach: Mach number
        :param altitude: (unit=m) altitude w.r.t. to sea level
        :param thrust_rate: thrust rate (unit=none)
        :param flight_phase: flight phase
        :return: a (N,) array with SFC values
        """
        return cls._interpolate_table(
            inputs, "private:propulsion:table:SFC", mach, altitude, thrust_rate, flight_phase
        )

    @classmethod
    def interpolate_thrust(
        cls,
        inputs: Mapping,
        mach: Union[float, Sequence[float]],
        altitude: Union[float, Sequence[float]],
        thrust_rate: Union[float, Sequence[float]],
        flight_phase: Union[FlightPhase, Sequence[FlightPhase]],
    ):
        """
        Convenience method for interpolating in thrust table provided by :meth:`compute`.

        Note: `mach`, `altitude`, `thrust_rate` and `flight_phase` must have the same size.

        :param inputs: a dict-like that provides OpenMDAO outputs from self.compute()
        :param mach: Mach number
        :param altitude: (unit=m) altitude w.r.t. to sea level
        :param thrust_rate: thrust rate (unit=none)
        :param flight_phase: flight phase
        :return: a (N,) array with thrust values
        """
        return cls._interpolate_table(
            inputs, "private:propulsion:table:thrust", mach, altitude, thrust_rate, flight_phase
        )

    @staticmethod
    def _interpolate_table(
        inputs,
        table_var_name,
        mach: Union[float, Sequence[float]],
        altitude: Union[float, Sequence[float]],
        thrust_rate: Union[float, Sequence[float]],
        flight_phase: Union[FlightPhase, Sequence[FlightPhase]],
    ):
        """
        Convenience method for interpolating values from tables provided by :meth:`compute`.

        Note: `mach`, `altitude`, `thrust_rate` and `flight_phase` must have the same size.

        :param inputs: a dict-like that provides OpenMDAO outputs from self.compute()
        :param table_var_name: the variable name for table where to interpolate
        :param mach: Mach number
        :param altitude: (unit=m) altitude w.r.t. to sea level
        :param thrust_rate: thrust rate (unit=none)
        :param flight_phase: flight phase
        :return: a (N,) array with values
        """

        mach_vector = inputs["private:propulsion:table:mach"]
        altitude_vector = inputs["private:propulsion:table:altitude"]
        thrust_rate_vector = inputs["private:propulsion:table:thrust_rate"]
        flight_phase_vector = inputs["private:propulsion:table:flight_phase"]
        table = inputs[table_var_name]

        flight_points = np.column_stack((mach, altitude, thrust_rate, flight_phase))

        interpolators = {}
        for phase in flight_phase_vector:
            interpolators[phase] = RegularGridInterpolator(
                (mach_vector, altitude_vector, thrust_rate_vector),
                table[:, :, :, flight_phase_vector == phase],
            )

        values = np.empty((flight_points.shape[0],), np.float)
        for phase in flight_phase_vector:
            phase_column = flight_points[:, 3]
            other_columns = flight_points[:, :3]
            values[phase_column == phase] = interpolators[phase](
                other_columns[phase_column == phase]
            ).squeeze()

        return values

    @classmethod
    def add_inputs(cls, me: Component):
        """
        Convenience method for easily adding inputs in setup() method.

        To be used in the setup() method of an OpenMDAO component that will use
        the engine table.
        It only use the needed add_inputs(). Partial derivatives are not handled
        here.

        :param me: an OpenMDAO Component instance
        """
        shape = cls._get_shape()
        me.add_input("private:propulsion:table:mach", np.nan, shape=shape[0])
        me.add_input("private:propulsion:table:altitude", np.nan, shape=shape[1], units="m")
        me.add_input("private:propulsion:table:thrust_rate", np.nan, shape=shape[2])
        me.add_input("private:propulsion:table:flight_phase", np.nan, shape=shape[3])
        me.add_input("private:propulsion:table:SFC", np.nan, shape=shape, units="kg/s/N")
        me.add_input("private:propulsion:table:thrust", np.nan, shape=shape, units="N")
