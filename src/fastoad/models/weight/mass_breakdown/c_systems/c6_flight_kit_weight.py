"""
Estimation of flight kit weight
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
import openmdao.api as om

from fastoad.constants import RangeCategory


class FlightKitWeight(om.ExplicitComponent):
    """
    Weight estimation for flight kit (tools that are always on board)

    Based on figures in :cite:`supaero:2014`, mass contribution C6
    """

    def setup(self):
        self.add_input("data:TLAR:range", val=np.nan, units="NM")
        self.add_input("tuning:weight:systems:flight_kit:mass:k", val=1.0)
        self.add_input("tuning:weight:systems:flight_kit:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:systems:flight_kit:mass", units="kg")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        tlar_range = inputs["data:TLAR:range"]
        k_c6 = inputs["tuning:weight:systems:flight_kit:mass:k"]
        offset_c6 = inputs["tuning:weight:systems:flight_kit:mass:offset"]

        if tlar_range <= RangeCategory.SHORT.max():
            temp_c6 = 10.0
        else:
            temp_c6 = 45.0

        outputs["data:weight:systems:flight_kit:mass"] = k_c6 * temp_c6 + offset_c6
