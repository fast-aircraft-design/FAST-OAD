"""
    Estimation of center of gravity for load case 1
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


class ComputeCGLoadCase1(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Center of gravity estimation for load case 1 """

    def setup(self):
        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:weight:payload:PAX:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:payload:rear_fret:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:payload:front_fret:CG:x", val=np.nan, units="m")
        self.add_input("data:TLAR:NPAX", val=np.nan)
        self.add_input("data:weight:aircraft_empty:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:aircraft_empty:mass", val=np.nan, units="m")

        self.add_output("data:weight:aircraft:load_case_1:CG:MAC_position")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        l0_wing = inputs["data:geometry:wing:MAC:length"]
        fa_length = inputs["data:geometry:wing:MAC:at25percent:x"]
        cg_pax = inputs["data:weight:payload:PAX:CG:x"]
        cg_rear_fret = inputs["data:weight:payload:rear_fret:CG:x"]
        cg_front_fret = inputs["data:weight:payload:front_fret:CG:x"]
        npax = inputs["data:TLAR:NPAX"]
        x_cg_plane_aft = inputs["data:weight:aircraft_empty:CG:x"]
        x_cg_plane_down = inputs["data:weight:aircraft_empty:mass"]
        x_cg_plane_up = x_cg_plane_aft * x_cg_plane_down

        # TODO: factorize the four load cases as they are relatively similar
        weight_pax = npax * 80.0
        weight_rear_fret = 1.0
        weight_front_fret = 0.0
        weight_pl = weight_pax + weight_rear_fret + weight_front_fret
        x_cg_pl_1 = (
            weight_pax * cg_pax
            + weight_rear_fret * cg_rear_fret
            + weight_front_fret * cg_front_fret
        ) / weight_pl
        x_cg_plane_pl_1 = (x_cg_plane_up + weight_pl * x_cg_pl_1) / (
            x_cg_plane_down + weight_pl
        )  # forward
        cg_ratio_pl_1 = (x_cg_plane_pl_1 - fa_length + 0.25 * l0_wing) / l0_wing

        outputs["data:weight:aircraft:load_case_1:CG:MAC_position"] = cg_ratio_pl_1
