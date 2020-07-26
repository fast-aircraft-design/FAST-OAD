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
from typing import Union

import numpy as np
import openmdao.api as om
import pandas as pd
from fastoad.base.flight_point import FlightPoint
from openmdao.core.component import Component


class IPropulsion(ABC):
    """
    Interface that should be implemented by propulsion models.
    """

    @abstractmethod
    def compute_flight_points(self, flight_points: Union[FlightPoint, pd.DataFrame]):
        """
        Computes Specific Fuel Consumption according to provided conditions.

        Each input can be a float, a list or an array.
        Inputs that are not floats must all have the same shape (numpy speaking).

        .. note:: **About use_thrust_rate, thrust_rate and thrust**

            :code:`thrust_is_regulated` tells if a flight point should be computed using
            :code:`thrust_rate` or :code:`thrust` as input. This way, the method can be used
            in a vectorized mode, where each point can be set to respect a **thrust** order or a
            **thrust rate** order.

            - if :code:`thrust_is_regulated` is :code:`None`, the considered input will be the
              provided one between :code:`thrust_rate` and :code:`thrust` (if both are provided,
              :code:`thrust_rate` will be used)

            - if :code:`thrust_is_regulated` is :code:`True` or :code:`False` (i.e., not a sequence),
              the considered input will be taken accordingly, and should of course not be None.

            - if :code:`thrust_is_regulated` is a sequence or array, :code:`thrust_rate` and
              :code:`thrust` should be provided and have the same shape as
              :code:`thrust_is_regulated:code:`. The method will consider for each element which input
              will be used according to :code:`thrust_is_regulated`.


        :param flight_points: FlightPoint instance(s)
        :return: None (inputs are updated in-place)
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

    def compute_flight_points(self, flight_points: Union[FlightPoint, pd.DataFrame]):

        if isinstance(flight_points, FlightPoint):
            flight_points_per_engine = FlightPoint(flight_points)
        else:
            flight_points_per_engine = flight_points.copy()

        if flight_points.thrust is not None:
            flight_points_per_engine.thrust = flight_points.thrust / self.engine_count

        self.engine.compute_flight_points(flight_points_per_engine)
        flight_points.sfc = flight_points_per_engine.sfc
        flight_points.thrust = flight_points_per_engine.thrust * self.engine_count
        flight_points.thrust_rate = flight_points_per_engine.thrust_rate


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
        self.add_input("data:propulsion:engine_setting", np.nan, shape=shape)
        self.add_input("data:propulsion:use_thrust_rate", np.nan, shape=shape)
        self.add_input("data:propulsion:required_thrust_rate", np.nan, shape=shape)
        self.add_input("data:propulsion:required_thrust", np.nan, shape=shape, units="N")

        self.add_output("data:propulsion:SFC", shape=shape, units="kg/s/N", ref=1e-4)
        self.add_output("data:propulsion:thrust_rate", shape=shape, lower=0.0, upper=1.0)
        self.add_output("data:propulsion:thrust", shape=shape, units="N", ref=1e5)

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        wrapper = self.get_wrapper().get_model(inputs)
        flight_point = FlightPoint(
            mach=inputs["data:propulsion:mach"],
            altitude=inputs["data:propulsion:altitude"],
            engine_setting=inputs["data:propulsion:engine_setting"],
            thrust_is_regulated=np.logical_not(
                inputs["data:propulsion:use_thrust_rate"].astype(int)
            ),
            thrust_rate=inputs["data:propulsion:required_thrust_rate"],
            thrust=inputs["data:propulsion:required_thrust"],
        )
        wrapper.compute_flight_points(flight_point)
        outputs["data:propulsion:SFC"] = flight_point.sfc
        outputs["data:propulsion:thrust_rate"] = flight_point.thrust_rate
        outputs["data:propulsion:thrust"] = flight_point.thrust

    @staticmethod
    @abstractmethod
    def get_wrapper() -> IOMPropulsionWrapper:
        """
        This method defines the used :class:`IOMPropulsionWrapper` instance.

        :return: an instance of OpenMDAO wrapper for propulsion model
        """
