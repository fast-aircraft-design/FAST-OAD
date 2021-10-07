"""
Estimation of power systems weight
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
from .constants import SERVICE_POWER_SYSTEMS_MASS


@RegisterSubmodel(SERVICE_POWER_SYSTEMS_MASS, "fastoad.submodel.weight.mass.systems.power.legacy")
class PowerSystemsWeight(om.ExplicitComponent):
    """
    Weight estimation for power systems (generation and distribution)

    This includes:

    - Auxiliary Power Unit (APU)
    - electric systems
    - hydraulic systems

    Based on formulas in :cite:`supaero:2014`, mass contribution C1
    """

    def setup(self):
        self.add_input("data:geometry:cabin:NPAX1", val=np.nan)
        self.add_input("data:weight:airframe:flight_controls:mass", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:MTOW", val=np.nan, units="kg")
        self.add_input("tuning:weight:systems:power:auxiliary_power_unit:mass:k", val=1.0)
        self.add_input(
            "tuning:weight:systems:power:auxiliary_power_unit:mass:offset", val=0.0, units="kg"
        )
        self.add_input("tuning:weight:systems:power:electric_systems:mass:k", val=1.0)
        self.add_input(
            "tuning:weight:systems:power:electric_systems:mass:offset", val=0.0, units="kg"
        )
        self.add_input("tuning:weight:systems:power:hydraulic_systems:mass:k", val=1.0)
        self.add_input(
            "tuning:weight:systems:power:hydraulic_systems:mass:offset", val=0.0, units="kg"
        )
        self.add_input("settings:weight:systems:power:mass:k_elec", val=1.0)

        self.add_output("data:weight:systems:power:auxiliary_power_unit:mass", units="kg")
        self.add_output("data:weight:systems:power:electric_systems:mass", units="kg")
        self.add_output("data:weight:systems:power:hydraulic_systems:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        npax1 = inputs["data:geometry:cabin:NPAX1"]
        flight_controls_weight = inputs["data:weight:airframe:flight_controls:mass"]
        mtow = inputs["data:weight:aircraft:MTOW"]
        k_c11 = inputs["tuning:weight:systems:power:auxiliary_power_unit:mass:k"]
        offset_c11 = inputs["tuning:weight:systems:power:auxiliary_power_unit:mass:offset"]
        k_c12 = inputs["tuning:weight:systems:power:electric_systems:mass:k"]
        offset_c12 = inputs["tuning:weight:systems:power:electric_systems:mass:offset"]
        k_c13 = inputs["tuning:weight:systems:power:hydraulic_systems:mass:k"]
        offset_c13 = inputs["tuning:weight:systems:power:hydraulic_systems:mass:offset"]
        k_elec = inputs["settings:weight:systems:power:mass:k_elec"]

        # Mass of auxiliary power unit
        temp_c11 = 11.3 * npax1 ** 0.64
        outputs["data:weight:systems:power:auxiliary_power_unit:mass"] = (
            k_c11 * temp_c11 + offset_c11
        )

        # Mass of electric system
        temp_c12 = k_elec * (0.444 * mtow ** 0.66 + 2.54 * npax1 + 0.254 * flight_controls_weight)
        outputs["data:weight:systems:power:electric_systems:mass"] = k_c12 * temp_c12 + offset_c12

        # Mass of the hydraulic system
        temp_c13 = k_elec * (0.256 * mtow ** 0.66 + 1.46 * npax1 + 0.146 * flight_controls_weight)
        outputs["data:weight:systems:power:hydraulic_systems:mass"] = k_c13 * temp_c13 + offset_c13
