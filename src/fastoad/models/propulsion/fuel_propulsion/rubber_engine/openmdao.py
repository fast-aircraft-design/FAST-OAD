"""OpenMDAO wrapping of RubberEngine."""
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

import numpy as np
from openmdao.core.component import Component

from fastoad.model_base.propulsion import (
    BaseOMPropulsionComponent,
    IOMPropulsionWrapper,
    IPropulsion,
)
from fastoad.module_management.service_registry import RegisterPropulsion
from fastoad.openmdao.validity_checker import ValidityDomainChecker
from .constants import RUBBER_ENGINE_DESCRIPTION
from .rubber_engine import RubberEngine


@RegisterPropulsion("fastoad.wrapper.propulsion.rubber_engine", desc=RUBBER_ENGINE_DESCRIPTION)
class OMRubberEngineWrapper(IOMPropulsionWrapper):
    """
    Wrapper class of for rubber engine model.

    It is made to allow a direct call to
    :class:`~fastoad.models.propulsion.fuel_propulsion.rubber_engine.rubber_engine.RubberEngine`
    in an OpenMDAO component.

    Example of usage of this class::

        import openmdao.api as om

        class MyComponent(om.ExplicitComponent):
            def initialize():
                self._engine_wrapper = OMRubberEngineWrapper()

            def setup():
                # Adds OpenMDAO variables that define the engine
                self._engine_wrapper.setup(self)

                # Do the normal setup
                self.add_input("my_input")
                [finish the setup...]

            def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
                [do something]

                # Get the engine instance, with parameters defined from OpenMDAO inputs
                engine = self._engine_wrapper.get_model(inputs)

                # Run the engine model. This is a pure Python call. You have to define
                # its inputs before, and to use its outputs according to your needs
                sfc, thrust_rate, thrust = engine.compute_flight_points(
                    mach,
                    altitude,
                    engine_setting,
                    use_thrust_rate,
                    thrust_rate,
                    thrust
                    )

                [do something else]

        )
    """

    def setup(self, component: Component):
        component.add_input("data:propulsion:rubber_engine:bypass_ratio", np.nan)
        component.add_input("data:propulsion:rubber_engine:overall_pressure_ratio", np.nan)
        component.add_input(
            "data:propulsion:rubber_engine:turbine_inlet_temperature", np.nan, units="K"
        )
        component.add_input("data:propulsion:MTO_thrust", np.nan, units="N")
        component.add_input("data:propulsion:rubber_engine:maximum_mach", np.nan)
        component.add_input("data:propulsion:rubber_engine:design_altitude", np.nan, units="m")
        component.add_input(
            "data:propulsion:rubber_engine:delta_t4_climb",
            -50,
            desc="As it is a delta, unit is K or °C, but is not "
            "specified to avoid OpenMDAO making unwanted conversion",
        )
        component.add_input(
            "data:propulsion:rubber_engine:delta_t4_cruise",
            -100,
            desc="As it is a delta, unit is K or °C, but is not "
            "specified to avoid OpenMDAO making unwanted conversion",
        )
        component.add_input("tuning:propulsion:rubber_engine:SFC:k_sl", 1.0)
        component.add_input("tuning:propulsion:rubber_engine:SFC:k_cr", 1.0)

    @staticmethod
    def get_model(inputs) -> IPropulsion:
        """

        :param inputs: input parameters that define the engine
        :return: a :class:`~fastoad.models.propulsion.fuel_propulsion.rubber_engine.rubber_engine.RubberEngine`
                 instance
        """
        engine_params = {
            "bypass_ratio": inputs["data:propulsion:rubber_engine:bypass_ratio"],
            "overall_pressure_ratio": inputs[
                "data:propulsion:rubber_engine:overall_pressure_ratio"
            ],
            "turbine_inlet_temperature": inputs[
                "data:propulsion:rubber_engine:turbine_inlet_temperature"
            ],
            "maximum_mach": inputs["data:propulsion:rubber_engine:maximum_mach"],
            "design_altitude": inputs["data:propulsion:rubber_engine:design_altitude"],
            "delta_t4_climb": inputs["data:propulsion:rubber_engine:delta_t4_climb"],
            "delta_t4_cruise": inputs["data:propulsion:rubber_engine:delta_t4_cruise"],
            "mto_thrust": inputs["data:propulsion:MTO_thrust"],
            "k_sfc_sl": inputs["tuning:propulsion:rubber_engine:SFC:k_sl"],
            "k_sfc_cr": inputs["tuning:propulsion:rubber_engine:SFC:k_cr"],
        }

        return RubberEngine(**engine_params)


@ValidityDomainChecker(
    {
        "data:propulsion:altitude": (None, 20000.0),
        "data:propulsion:mach": (0.75, 0.85),  # limitation of SFC ratio model
        "data:propulsion:rubber_engine:overall_pressure_ratio": (20.0, 40.0),
        "data:propulsion:rubber_engine:bypass_ratio": (3.0, 6.0),
        "data:propulsion:thrust_rate": (0.5, 1.0),  # limitation of SFC ratio model
        "data:propulsion:rubber_engine:turbine_inlet_temperature": (
            1400.0,
            1600.0,
        ),  # limitation of max thrust model
        "data:propulsion:rubber_engine:delta_t4_climb": (
            -100.0,
            0.0,
        ),  # limitation of max thrust model
        "data:propulsion:rubber_engine:delta_t4_cruise": (
            -100.0,
            0.0,
        ),  # limitation of max thrust model
    }
)
# @RegisterOpenMDAOSystem(
#     "fastoad.propulsion.rubber_engine",
#     desc=RUBBER_ENGINE_DESCRIPTION,
#     domain=ModelDomain.PROPULSION,
# )
class OMRubberEngineComponent(BaseOMPropulsionComponent):
    """
    Parametric engine model as OpenMDAO component

    See
    :class:`~fastoad.models.propulsion.fuel_propulsion.rubber_engine.rubber_engine.RubberEngine`
    for more information.
    """

    def setup(self):
        super().setup()
        self.get_wrapper().setup(self)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    @staticmethod
    def get_wrapper() -> OMRubberEngineWrapper:
        return OMRubberEngineWrapper()
