"""
Estimation of cargo configuration weight
"""
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
import openmdao.api as om

from fastoad.module_management.service_registry import RegisterSubmodel
from .constants import SERVICE_CARGO_CONFIGURATION_MASS


@RegisterSubmodel(
    SERVICE_CARGO_CONFIGURATION_MASS, "service.mass.furniture.cargo_configuration.legacy"
)
class CargoConfigurationWeight(om.ExplicitComponent):
    """
    Weight estimation for equipments for freight transport (applies only for freighters)

    Based on :cite:`supaero:2014`, mass contribution D1
    """

    def setup(self):
        self.add_input("data:geometry:cabin:NPAX1", val=np.nan)
        self.add_input("data:geometry:cabin:containers:count", val=np.nan)
        self.add_input("data:geometry:cabin:pallet_count", val=np.nan)
        self.add_input("data:geometry:cabin:seats:economical:count_by_row", val=np.nan)
        self.add_input("tuning:weight:furniture:cargo_configuration:mass:k", val=1.0)
        self.add_input(
            "tuning:weight:furniture:cargo_configuration:mass:offset", val=0.0, units="kg"
        )

        self.add_output("data:weight:furniture:cargo_configuration:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        npax1 = inputs["data:geometry:cabin:NPAX1"]
        side_by_side_eco_seat_count = inputs["data:geometry:cabin:seats:economical:count_by_row"]
        container_count = inputs["data:geometry:cabin:containers:count"]
        pallet_number = inputs["data:geometry:cabin:pallet_count"]
        k_d1 = inputs["tuning:weight:furniture:cargo_configuration:mass:k"]
        offset_d1 = inputs["tuning:weight:furniture:cargo_configuration:mass:offset"]

        if side_by_side_eco_seat_count <= 6.0:
            temp_d1 = 0.351 * (npax1 - 38)
        else:
            temp_d1 = 85 * container_count + 110 * pallet_number
        outputs["data:weight:furniture:cargo_configuration:mass"] = k_d1 * temp_d1 + offset_d1
