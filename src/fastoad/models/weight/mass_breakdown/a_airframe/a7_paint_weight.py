"""
Estimation of paint weight
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
from .constants import SERVICE_PAINT_MASS


@RegisterSubmodel(SERVICE_PAINT_MASS, "fastoad.submodel.weight.mass.airframe.paint.legacy")
class PaintWeight(om.ExplicitComponent):
    """
    Weight estimation for paint

    Based on formula in :cite:`supaero:2014`, mass contribution A7
    """

    def setup(self):
        self.add_input("data:geometry:aircraft:wetted_area", val=np.nan, units="m**2")
        self.add_input("tuning:weight:airframe:paint:mass:k", val=1.0)
        self.add_input("tuning:weight:airframe:paint:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:airframe:paint:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        total_wet_surface = inputs["data:geometry:aircraft:wetted_area"]
        k_a7 = inputs["tuning:weight:airframe:paint:mass:k"]
        offset_a7 = inputs["tuning:weight:airframe:paint:mass:offset"]

        temp_a7 = 0.180 * total_wet_surface
        outputs["data:weight:airframe:paint:mass"] = k_a7 * temp_a7 + offset_a7
