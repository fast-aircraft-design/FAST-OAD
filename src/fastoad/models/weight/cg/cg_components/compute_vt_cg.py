"""
    Estimation of vertical tail center of gravity
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
from ..constants import SERVICE_VERTICAL_TAIL_CG


@RegisterSubmodel(SERVICE_VERTICAL_TAIL_CG, "fastoad.submodel.weight.cg.vertical_tail.legacy")
class ComputeVTcg(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Vertical tail center of gravity estimation"""

    def setup(self):
        self.add_input("data:geometry:vertical_tail:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:vertical_tail:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:vertical_tail:tip:chord", val=np.nan, units="m")
        self.add_input(
            "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan, units="m"
        )
        self.add_input("data:geometry:vertical_tail:MAC:at25percent:x:local", val=np.nan, units="m")
        self.add_input("data:geometry:vertical_tail:sweep_25", val=np.nan, units="deg")
        self.add_input("data:geometry:vertical_tail:span", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")

        self.add_output("data:weight:airframe:vertical_tail:CG:x", units="m")

    def setup_partials(self):
        self.declare_partials("data:weight:airframe:vertical_tail:CG:x", "*", method="fd")

    def compute(self, inputs, outputs):
        root_chord = inputs["data:geometry:vertical_tail:root:chord"]
        tip_chord = inputs["data:geometry:vertical_tail:tip:chord"]
        lp_vt = inputs["data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25"]
        mac_vt = inputs["data:geometry:vertical_tail:MAC:length"]
        fa_length = inputs["data:geometry:wing:MAC:at25percent:x"]
        x0_vt = inputs["data:geometry:vertical_tail:MAC:at25percent:x:local"]
        sweep_25_vt = inputs["data:geometry:vertical_tail:sweep_25"]
        b_v = inputs["data:geometry:vertical_tail:span"]

        tmp = root_chord * 0.25 + b_v * math.tan(sweep_25_vt / 180.0 * math.pi) - tip_chord * 0.25
        l_cg_vt = (1 - 0.55) * (root_chord - tip_chord) + tip_chord
        x_cg_vt = 0.42 * l_cg_vt + 0.55 * tmp
        x_cg_vt_absolute = lp_vt + fa_length - 0.25 * mac_vt + (x_cg_vt - x0_vt)

        outputs["data:weight:airframe:vertical_tail:CG:x"] = x_cg_vt_absolute
