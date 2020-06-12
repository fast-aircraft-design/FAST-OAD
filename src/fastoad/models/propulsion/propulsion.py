"""Base module for propulsion models."""
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
from openmdao.core.component import Component


class IPropulsion(ABC):
    """
    Interface that should be implemented by propulsion models.
    """

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


class EngineSet(IPropulsion):
    def __init__(self, engine: IPropulsion, engine_count):
        """
        Class for modelling an assembly of identical engines.

        Thrust is supposed equally distributed among them.

        :param engine: the engine model
        :param engine_count:
        """
        self.engine = engine
        self.engine_count = engine_count

    def compute_flight_points(
        self,
        mach: Union[float, Sequence],
        altitude: Union[float, Sequence],
        phase: Union[FlightPhase, Sequence],
        use_thrust_rate: Optional[Union[bool, Sequence]] = None,
        thrust_rate: Optional[Union[float, Sequence]] = None,
        thrust: Optional[Union[float, Sequence]] = None,
    ) -> Tuple[Union[float, Sequence], Union[float, Sequence], Union[float, Sequence]]:

        if thrust is not None:
            thrust = thrust / self.engine_count

        sfc, thrust_rate, thrust = self.engine.compute_flight_points(
            mach, altitude, phase, use_thrust_rate, thrust_rate, thrust
        )
        return sfc, thrust_rate, thrust * self.engine_count


class IOMPropulsionWrapper:
    """
    Interface for wrapping a :class:`IPropulsion` subclass in OpenMDAO.

    The implementation class defines the needed input variables for instantiating the
    :class:`IPropulsion` subclass in :meth:`setup` and use them for instantiation in
    :meth:`get_model`

    see :class:`~fastoad.models.propulsion.fuel_propulsion.rubber_engine.OMRubberEngineWrapper` for
    an example of implementation.
    """

    @abstractmethod
    def setup(self, component: Component):
        """
        Defines the needed OpenMDAO inputs for propulsion instantiation as done in :meth:`get_model`

        Use `add_inputs` and `declare_partials` methods of the provided `component`

        :param component:
        """

    @staticmethod
    @abstractmethod
    def get_model(inputs) -> IPropulsion:
        """
        This method defines the used :class:`IPropulsion` subclass instance.

        :param inputs: OpenMDAO input vector where the parameters that define the
                       propulsion model are
        :return: the propulsion model instance
        """


class BaseOMPropulsionComponent(om.ExplicitComponent, ABC):
    """
    Base class for OpenMDAO wrapping of subclasses of :class:`IEngineForOpenMDAO`.

    Classes that implements this interface should add their own inputs in setup()
    and implement :meth:`get_wrapper`.
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

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        wrapper = self.get_wrapper().get_model(inputs)
        sfc, thrust_rate, thrust = wrapper.compute_flight_points(
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
    def get_wrapper() -> IOMPropulsionWrapper:
        """
        This method defines the used :class:`IOMPropulsionWrapper` instance.

        :return: an instance of OpenMDAO wrapper for propulsion model
        """
