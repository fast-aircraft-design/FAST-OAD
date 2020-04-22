"""
Estimation of fuel lines weight
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
from openmdao.core.explicitcomponent import ExplicitComponent


class UnconsumablesWeight(ExplicitComponent):
    """
    Weight estimation for oil and unusable fuel

    Based on formula in :cite:`supaero:2014`, mass contribution B3
    """

    def setup(self):
        self.add_input("data:geometry:propulsion:engine:count", val=np.nan)
        self.add_input("data:weight:aircraft:MFW", val=np.nan, units="kg")
        self.add_input("tuning:weight:propulsion:unconsumables:mass:k", val=1.0)
        self.add_input("tuning:weight:propulsion:unconsumables:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:propulsion:unconsumables:mass", units="kg")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        n_engines = inputs["data:geometry:propulsion:engine:count"]
        mfw = inputs["data:weight:aircraft:MFW"]
        k_b3 = inputs["tuning:weight:propulsion:unconsumables:mass:k"]
        offset_b3 = inputs["tuning:weight:propulsion:unconsumables:mass:offset"]

        temp_b3 = 25 * n_engines + 0.0035 * mfw
        outputs["data:weight:propulsion:unconsumables:mass"] = k_b3 * temp_b3 + offset_b3
