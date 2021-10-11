"""
    Estimation of horizontal tail center of gravity
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

import math

import numpy as np
import openmdao.api as om

from fastoad.module_management.service_registry import RegisterSubmodel
from ..constants import SERVICE_HORIZONTAL_TAIL_CG


@RegisterSubmodel(SERVICE_HORIZONTAL_TAIL_CG, "fastoad.submodel.weight.cg.horizontal_tail.legacy")
class ComputeHTcg(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Horizontal tail center of gravity estimation"""

    def setup(self):
        self.add_input("data:geometry:horizontal_tail:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:tip:chord", val=np.nan, units="m")
        self.add_input(
            "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan, units="m"
        )
        self.add_input("data:geometry:horizontal_tail:span", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:sweep_25", val=np.nan, units="deg")
        self.add_input("data:geometry:horizontal_tail:MAC:length", val=np.nan, units="m")
        self.add_input(
            "data:geometry:horizontal_tail:MAC:at25percent:x:local", val=np.nan, units="m"
        )

        self.add_output("data:weight:airframe:horizontal_tail:CG:x", units="m")

    def setup_partials(self):
        self.declare_partials("data:weight:airframe:horizontal_tail:CG:x", "*", method="fd")

    def compute(self, inputs, outputs):
        root_chord = inputs["data:geometry:horizontal_tail:root:chord"]
        tip_chord = inputs["data:geometry:horizontal_tail:tip:chord"]
        b_h = inputs["data:geometry:horizontal_tail:span"]
        sweep_25_ht = inputs["data:geometry:horizontal_tail:sweep_25"]
        fa_length = inputs["data:geometry:wing:MAC:at25percent:x"]
        lp_ht = inputs["data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"]
        mac_ht = inputs["data:geometry:horizontal_tail:MAC:length"]
        x0_ht = inputs["data:geometry:horizontal_tail:MAC:at25percent:x:local"]

        tmp = (
            root_chord * 0.25 + b_h / 2 * math.tan(sweep_25_ht / 180.0 * math.pi) - tip_chord * 0.25
        )

        l_cg = 0.62 * (root_chord - tip_chord) + tip_chord
        x_cg_ht = 0.42 * l_cg + 0.38 * tmp
        x_cg_ht_absolute = lp_ht + fa_length - 0.25 * mac_ht + (x_cg_ht - x0_ht)

        outputs["data:weight:airframe:horizontal_tail:CG:x"] = x_cg_ht_absolute
