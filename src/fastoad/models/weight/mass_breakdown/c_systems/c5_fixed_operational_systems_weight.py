"""
Estimation of fixed operational systems weight
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
from .constants import SERVICE_FIXED_OPERATIONAL_SYSTEMS_MASS


@RegisterSubmodel(
    SERVICE_FIXED_OPERATIONAL_SYSTEMS_MASS,
    "fastoad.submodel.weight.mass.systems.fixed_operational.legacy",
)
class FixedOperationalSystemsWeight(om.ExplicitComponent):
    """
    Weight estimation for fixed operational systems (weather radar, flight recorder, ...)

    Based on formulas in :cite:`supaero:2014`, mass contribution C5
    """

    def setup(self):
        self.add_input("data:geometry:fuselage:front_length", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:rear_length", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:length", val=np.nan, units="m")
        self.add_input("data:geometry:cabin:seats:economical:count_by_row", val=np.nan)
        self.add_input("data:geometry:wing:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:cabin:containers:count_by_row", val=np.nan)
        self.add_input("tuning:weight:systems:operational:mass:k", val=1.0)
        self.add_input("tuning:weight:systems:operational:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:systems:operational:radar:mass", units="kg")
        self.add_output("data:weight:systems:operational:cargo_hold:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        front_section_length = inputs["data:geometry:fuselage:front_length"]
        aft_section_length = inputs["data:geometry:fuselage:rear_length"]
        fuselage_length = inputs["data:geometry:fuselage:length"]
        front_seat_number_eco = inputs["data:geometry:cabin:seats:economical:count_by_row"]
        l2_wing = inputs["data:geometry:wing:root:chord"]
        side_by_side_container_number = inputs["data:geometry:cabin:containers:count_by_row"]
        k_c5 = inputs["tuning:weight:systems:operational:mass:k"]
        offset_c5 = inputs["tuning:weight:systems:operational:mass:offset"]

        cylindrical_section_length = fuselage_length - front_section_length - aft_section_length

        cargo_compartment_length = (
            cylindrical_section_length + 0.864 * (front_seat_number_eco - 5) - 0.8 * l2_wing
        )

        # Radar
        temp_c51 = 100.0
        outputs["data:weight:systems:operational:radar:mass"] = k_c5 * temp_c51 + offset_c5

        # Cargo container systems
        temp_c52 = 23.4 * cargo_compartment_length * side_by_side_container_number
        outputs["data:weight:systems:operational:cargo_hold:mass"] = k_c5 * temp_c52 + offset_c5
