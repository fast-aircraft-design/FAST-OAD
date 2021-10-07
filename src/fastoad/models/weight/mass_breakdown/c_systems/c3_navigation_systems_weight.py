"""
Estimation of navigation systems weight
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

from fastoad.constants import RangeCategory
from fastoad.module_management.service_registry import RegisterSubmodel
from .constants import SERVICE_NAVIGATION_SYSTEMS_MASS


@RegisterSubmodel(
    SERVICE_NAVIGATION_SYSTEMS_MASS, "fastoad.submodel.weight.mass.systems.navigation.legacy"
)
class NavigationSystemsWeight(om.ExplicitComponent):
    """
    Weight estimation for navigation systems

    Based on figures in :cite:`supaero:2014`, mass contribution C3
    """

    def setup(self):
        self.add_input("data:TLAR:range", val=np.nan, units="NM")
        self.add_input("data:geometry:fuselage:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:b_50", val=np.nan, units="m")
        self.add_input("tuning:weight:systems:navigation:mass:k", val=1.0)
        self.add_input("tuning:weight:systems:navigation:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:systems:navigation:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        tlar_range = inputs["data:TLAR:range"]
        fuselage_length = inputs["data:geometry:fuselage:length"]
        b_50 = inputs["data:geometry:wing:b_50"]
        k_c3 = inputs["tuning:weight:systems:navigation:mass:k"]
        offset_c3 = inputs["tuning:weight:systems:navigation:mass:offset"]

        if tlar_range in RangeCategory.SHORT:
            base_weight = 150.0
        elif tlar_range in RangeCategory.SHORT_MEDIUM:
            base_weight = 450.0
        elif tlar_range in RangeCategory.MEDIUM:
            base_weight = 700.0
        else:
            base_weight = 800.0

        temp_c3 = base_weight + 0.033 * fuselage_length * b_50
        outputs["data:weight:systems:navigation:mass"] = k_c3 * temp_c3 + offset_c3
