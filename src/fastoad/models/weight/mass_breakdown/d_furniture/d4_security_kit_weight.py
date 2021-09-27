"""
Estimation of security kit weight
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
from .constants import SERVICE_SECURITY_KIT_MASS


@RegisterSubmodel(SERVICE_SECURITY_KIT_MASS, "service.mass.furniture.security_kit.legacy")
class SecurityKitWeight(om.ExplicitComponent):
    """
    Weight estimation for security kit

    Based on :cite:`supaero:2014`, mass contribution D4
    """

    """ Passenger security kit weight estimation (D4) """

    def setup(self):
        self.add_input("data:TLAR:NPAX", val=np.nan)
        self.add_input("tuning:weight:furniture:security_kit:mass:k", val=1.0)
        self.add_input("tuning:weight:furniture:security_kit:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:furniture:security_kit:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        npax = inputs["data:TLAR:NPAX"]
        k_d4 = inputs["tuning:weight:furniture:security_kit:mass:k"]
        offset_d4 = inputs["tuning:weight:furniture:security_kit:mass:offset"]

        temp_d4 = 1.5 * npax
        outputs["data:weight:furniture:security_kit:mass"] = k_d4 * temp_d4 + offset_d4
