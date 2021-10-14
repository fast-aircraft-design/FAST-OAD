"""
    Estimation of main landing gear center of gravity
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
from ..constants import SERVICE_MLG_CG


@RegisterSubmodel(SERVICE_MLG_CG, "fastoad.submodel.weight.cg.main_landing_gear")
class UpdateMLG(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Main landing gear center of gravity estimation"""

    def setup(self):
        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:weight:aircraft:CG:aft:MAC_position", val=np.nan)
        self.add_input("data:weight:airframe:landing_gear:front:CG:x", units="m")
        self.add_input("settings:weight:airframe:landing_gear:front:weight_ratio", val=0.08)

        self.add_output("data:weight:airframe:landing_gear:main:CG:x", units="m")

    def setup_partials(self):
        self.declare_partials("data:weight:airframe:landing_gear:main:CG:x", "*", method="fd")

    def compute(self, inputs, outputs):
        l0_wing = inputs["data:geometry:wing:MAC:length"]
        fa_length = inputs["data:geometry:wing:MAC:at25percent:x"]
        cg_ratio = inputs["data:weight:aircraft:CG:aft:MAC_position"]
        cg_a52 = inputs["data:weight:airframe:landing_gear:front:CG:x"]
        front_lg_weight_ratio = inputs["settings:weight:airframe:landing_gear:front:weight_ratio"]

        x_cg = fa_length - 0.25 * l0_wing + cg_ratio * l0_wing

        cg_a51 = (x_cg - front_lg_weight_ratio * cg_a52) / (1 - front_lg_weight_ratio)

        outputs["data:weight:airframe:landing_gear:main:CG:x"] = cg_a51
