#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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


class DummyEngine(AbstractFuelPropulsion):
    def __init__(self, max_thrust, max_sfc):
        """
        Dummy engine model.

        Max thrust does not depend on flight conditions.
        SFC varies linearly with thrust_rate, from max_sfc/2. when thrust rate is 0.,
        to max_sfc when thrust_rate is 1.0

        :param max_thrust: thrust when thrust rate = 1.0
        :param max_sfc: SFC when thrust rate = 1.0
        """
        self.max_thrust = max_thrust
        self.max_sfc = max_sfc

    def compute_flight_points(self, flight_point: FlightPoint):
        if flight_point.thrust_is_regulated or flight_point.thrust_rate is None:
            flight_point.thrust_rate = flight_point.thrust / self.max_thrust
        else:
            flight_point.thrust = self.max_thrust * flight_point.thrust_rate

        flight_point.sfc = self.max_sfc * (1.0 + flight_point.thrust_rate) / 2.0


@RegisterPropulsion("test.wrapper.propulsion.dummy_engine")
class DummyEngineWrapper(IOMPropulsionWrapper):
    def setup(self, component: Component):
        component.add_input("data:propulsion:dummy_engine:max_thrust", 1.2e5, units="N")
        component.add_input("data:propulsion:dummy_engine:max_sfc", 1.5e-5, units="kg/N/s")
        component.add_input("data:geometry:propulsion:engine_count", 2, units="unitless")

    def get_model(self, inputs) -> IPropulsion:
        return FuelEngineSet(
            DummyEngine(
                inputs["data:propulsion:dummy_engine:max_thrust"],
                inputs["data:propulsion:dummy_engine:max_sfc"],
            ),
            inputs["data:geometry:propulsion:engine_count"],
        )
