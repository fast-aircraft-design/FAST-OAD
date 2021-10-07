"""
Estimation of transmissions systems weight
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
from .constants import SERVICE_TRANSMISSION_SYSTEMS_MASS


@RegisterSubmodel(
    SERVICE_TRANSMISSION_SYSTEMS_MASS, "fastoad.submodel.weight.mass.systems.transmission.legacy"
)
class TransmissionSystemsWeight(om.ExplicitComponent):
    """
    Weight estimation for transmission systems

    Based on figures in :cite:`supaero:2014`, mass contribution C4
    """

    def setup(self):
        self.add_input("data:TLAR:range", val=np.nan, units="NM")
        self.add_input("tuning:weight:systems:transmission:mass:k", val=1.0)
        self.add_input("tuning:weight:systems:transmission:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:systems:transmission:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        tlar_range = inputs["data:TLAR:range"]
        k_c4 = inputs["tuning:weight:systems:transmission:mass:k"]
        offset_c4 = inputs["tuning:weight:systems:transmission:mass:offset"]

        if tlar_range in RangeCategory.SHORT:
            temp_c4 = 100.0
        elif tlar_range in RangeCategory.SHORT_MEDIUM:
            temp_c4 = 200.0
        elif tlar_range in RangeCategory.MEDIUM:
            temp_c4 = 250.0
        else:
            temp_c4 = 350.0

        outputs["data:weight:systems:transmission:mass"] = k_c4 * temp_c4 + offset_c4
