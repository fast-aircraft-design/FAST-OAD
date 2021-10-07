"""
Estimation of toilets weight
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
from .constants import SERVICE_TOILETS_MASS


@RegisterSubmodel(SERVICE_TOILETS_MASS, "service.mass.furniture.toilets.legacy")
class ToiletsWeight(om.ExplicitComponent):
    """
    Weight estimation for toilets

    Based on :cite:`supaero:2014`, mass contribution D5
    """

    def setup(self):
        self.add_input("data:TLAR:range", val=np.nan, units="NM")
        self.add_input("data:TLAR:NPAX", val=np.nan)
        self.add_input("tuning:weight:furniture:toilets:mass:k", val=1.0)
        self.add_input("tuning:weight:furniture:toilets:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:furniture:toilets:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        tlar_range = inputs["data:TLAR:range"]
        npax = inputs["data:TLAR:NPAX"]
        k_d5 = inputs["tuning:weight:furniture:toilets:mass:k"]
        offset_d5 = inputs["tuning:weight:furniture:toilets:mass:offset"]

        if tlar_range in RangeCategory.SHORT:
            k_toilet = 0.1
        elif tlar_range in RangeCategory.SHORT_MEDIUM:
            k_toilet = 0.5
        elif tlar_range in RangeCategory.MEDIUM:
            k_toilet = 1.0
        else:
            k_toilet = 1.5

        temp_d5 = k_toilet * npax
        outputs["data:weight:furniture:toilets:mass"] = k_d5 * temp_d5 + offset_d5
