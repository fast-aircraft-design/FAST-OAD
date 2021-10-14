"""
Estimation of landing gear weight
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
from .constants import SERVICE_LANDING_GEARS_MASS


@RegisterSubmodel(
    SERVICE_LANDING_GEARS_MASS, "fastoad.submodel.weight.mass.airframe.landing_gears.legacy"
)
class LandingGearWeight(om.ExplicitComponent):
    """
    Weight estimation for landing gears

    Based on formulas in :cite:`supaero:2014`, mass contribution A5
    """

    def setup(self):
        self.add_input("data:weight:aircraft:MTOW", val=np.nan, units="kg")
        self.add_input("tuning:weight:airframe:landing_gear:mass:k", val=1.0)
        self.add_input("tuning:weight:airframe:landing_gear:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:airframe:landing_gear:main:mass", units="kg")
        self.add_output("data:weight:airframe:landing_gear:front:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        mtow = inputs["data:weight:aircraft:MTOW"]
        k_a5 = inputs["tuning:weight:airframe:landing_gear:mass:k"]
        offset_a5 = inputs["tuning:weight:airframe:landing_gear:mass:offset"]

        temp_a51 = 18.1 + 0.131 * mtow ** 0.75 + 0.019 * mtow + 2.23e-5 * mtow ** 1.5
        temp_a52 = 9.1 + 0.082 * mtow ** 0.75 + 2.97e-6 * mtow ** 1.5

        a51 = k_a5 * temp_a51 + offset_a5
        a52 = k_a5 * temp_a52 + offset_a5

        outputs["data:weight:airframe:landing_gear:main:mass"] = a51
        outputs["data:weight:airframe:landing_gear:front:mass"] = a52
