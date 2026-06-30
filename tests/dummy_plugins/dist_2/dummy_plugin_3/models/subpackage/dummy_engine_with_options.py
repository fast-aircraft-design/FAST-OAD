#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2026 ONERA & ISAE-SUPAERO
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

from openmdao.core.component import Component

from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import (
    AbstractFuelPropulsion,
    FuelEngineSet,
    IOMPropulsionWrapper,
    IPropulsion,
)
from fastoad.module_management.service_registry import RegisterPropulsion


class DummyEngineLowFidelity(AbstractFuelPropulsion):
    def __init__(self, max_thrust, sfc):
        """
        Dummy engine model.

        Max thrust does not depend on flight conditions.
        SFC is constant

        :param max_thrust: thrust when thrust rate = 1.0
        :param sfc: SFC
        """
        self.max_thrust = max_thrust
        self.sfc = sfc

    def compute_flight_points(self, flight_point: FlightPoint):
        if flight_point.thrust_is_regulated or flight_point.thrust_rate is None:
            flight_point.thrust_rate = flight_point.thrust / self.max_thrust
        else:
            flight_point.thrust = self.max_thrust * flight_point.thrust_rate

        flight_point.sfc = self.sfc


class DummyEngineHighFidelity(AbstractFuelPropulsion):
    def __init__(self, max_thrust, sfc_min_thrust_rate, sfc_max_thrust_rate):
        """
        Dummy engine model.

        Max thrust does not depend on flight conditions.
        SFC varies linearly between a value when thrust rate is nil and another value when thrust
        rate is at 1.

        :param max_thrust: thrust when thrust rate = 1.0
        :param sfc_min_thrust_rate: SFC at minimum thrust rate
        :param sfc_max_thrust_rate: SFC at maximum thrust rate
        """
        self.max_thrust = max_thrust
        self.sfc_min_thrust_rate = sfc_min_thrust_rate
        self.sfc_max_thrust_rate = sfc_max_thrust_rate

    def compute_flight_points(self, flight_point: FlightPoint):
        if flight_point.thrust_is_regulated or flight_point.thrust_rate is None:
            flight_point.thrust_rate = flight_point.thrust / self.max_thrust
        else:
            flight_point.thrust = self.max_thrust * flight_point.thrust_rate

        flight_point.sfc = self.sfc_min_thrust_rate + (
                self.sfc_max_thrust_rate - self.sfc_min_thrust_rate
        ) * flight_point.thrust_rate


@RegisterPropulsion("test.wrapper.propulsion.dummy_engine_with_options")
class DummyEngineWrapper(IOMPropulsionWrapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gas_turbine_fidelity = "low_fidelity"  # By default

    def setup(self, component: Component):

        component.add_input("data:propulsion:dummy_engine:max_thrust", 1.2e5, units="N")
        component.add_input("data:geometry:propulsion:engine_count", 2, units="unitless")

        if component.options["propulsion_options"].get("gas_turbine_fidelity", None) == "high_fidelity":
            self.gas_turbine_fidelity = "high_fidelity"
            component.add_input("data:propulsion:dummy_engine:sfc_min_thrust_rate", 1.5e-5, units="kg/N/s")
            component.add_input("data:propulsion:dummy_engine:sfc_max_thrust_rate", 0.75e-5, units="kg/N/s")
        else:
            self.gas_turbine_fidelity = "low_fidelity"
            component.add_input("data:propulsion:dummy_engine:sfc", 1.5e-5, units="kg/N/s")

    def get_model(self, inputs) -> IPropulsion:
        if self.gas_turbine_fidelity == "high_fidelity":
            return FuelEngineSet(
                DummyEngineHighFidelity(
                    inputs["data:propulsion:dummy_engine:max_thrust"],
                    inputs["data:propulsion:dummy_engine:sfc_min_thrust_rate"],
                    inputs["data:propulsion:dummy_engine:sfc_max_thrust_rate"],
                ),
                inputs["data:geometry:propulsion:engine_count"],
            )
        else:
            return FuelEngineSet(
                DummyEngineLowFidelity(
                    inputs["data:propulsion:dummy_engine:max_thrust"],
                    inputs["data:propulsion:dummy_engine:sfc"],
                ),
                inputs["data:geometry:propulsion:engine_count"],
            )
