"""
    Estimation of vertical tail distance
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


class ComputeVTDistance(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Vertical tail distance estimation"""

    def setup(self):

        self.add_input("data:geometry:fuselage:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:geometry:has_T_tail", val=np.nan)

        self.add_output("data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25", units="m")

    def setup_partials(self):
        self.declare_partials(
            "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25",
            ["data:geometry:fuselage:length", "data:geometry:wing:MAC:at25percent:x"],
            method="fd",
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        tail_type = np.round(inputs["data:geometry:has_T_tail"])
        fus_length = inputs["data:geometry:fuselage:length"]
        fa_length = inputs["data:geometry:wing:MAC:at25percent:x"]

        if tail_type == 1:
            lp_vt = 0.93 * fus_length - fa_length
        elif tail_type == 0:
            lp_vt = 0.88 * fus_length - fa_length
        else:
            raise ValueError("Value of data:geometry:has_T_tail can only be 0 or 1")

        outputs["data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25"] = lp_vt
