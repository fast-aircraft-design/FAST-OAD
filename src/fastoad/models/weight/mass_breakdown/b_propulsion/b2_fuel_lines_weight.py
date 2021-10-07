"""
Estimation of fuel lines weight
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
from .constants import SERVICE_FUEL_LINES_MASS


@RegisterSubmodel(
    SERVICE_FUEL_LINES_MASS, "fastoad.submodel.weight.mass.propulsion.fuel_lines.legacy"
)
class FuelLinesWeight(om.ExplicitComponent):
    """
    Weight estimation for fuel lines

    Based on formula in :cite:`supaero:2014`, mass contribution B2
    """

    def setup(self):
        self.add_input("data:geometry:wing:b_50", val=np.nan, units="m")
        self.add_input("data:weight:aircraft:MFW", val=np.nan, units="kg")
        self.add_input("data:weight:propulsion:engine:mass", val=np.nan, units="kg")
        self.add_input("tuning:weight:propulsion:fuel_lines:mass:k", val=1.0)
        self.add_input("tuning:weight:propulsion:fuel_lines:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:propulsion:fuel_lines:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        b_50 = inputs["data:geometry:wing:b_50"]
        mfw = inputs["data:weight:aircraft:MFW"]
        k_b2 = inputs["tuning:weight:propulsion:fuel_lines:mass:k"]
        offset_b2 = inputs["tuning:weight:propulsion:fuel_lines:mass:offset"]
        weight_engines = inputs["data:weight:propulsion:engine:mass"]

        temp_b2 = 0.02 * weight_engines + 2.0 * b_50 + 0.35 * mfw ** 0.66
        outputs["data:weight:propulsion:fuel_lines:mass"] = k_b2 * temp_b2 + offset_b2
