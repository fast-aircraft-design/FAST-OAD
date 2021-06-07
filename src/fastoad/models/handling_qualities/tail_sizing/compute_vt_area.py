"""
Estimation of vertical tail area
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


class ComputeVTArea(om.ExplicitComponent):
    """
    Computes area of vertical tail plane

    Area is computed to fulfill lateral stability requirement (with the most aft CG)
    as stated in :cite:raymer:1992.
    """

    def setup(self):
        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:weight:aircraft:CG:aft:MAC_position", val=np.nan)
        self.add_input("data:aerodynamics:fuselage:cruise:CnBeta", val=np.nan)
        self.add_input("data:aerodynamics:vertical_tail:cruise:CL_alpha", val=np.nan)
        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")
        self.add_input(
            "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan, units="m"
        )

        self.add_output("data:geometry:vertical_tail:wetted_area", units="m**2", ref=100.0)
        self.add_output("data:geometry:vertical_tail:area", units="m**2", ref=50.0)
        self.add_output("data:aerodynamics:vertical_tail:cruise:CnBeta", units="m**2")

    def setup_partials(self):
        self.declare_partials("data:geometry:vertical_tail:wetted_area", "*", method="fd")
        self.declare_partials("data:geometry:vertical_tail:area", "*", method="fd")
        self.declare_partials("data:aerodynamics:vertical_tail:cruise:CnBeta", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        # pylint: disable=too-many-locals  # needed for clarity

        wing_area = inputs["data:geometry:wing:area"]
        span = inputs["data:geometry:wing:span"]
        l0_wing = inputs["data:geometry:wing:MAC:length"]
        cg_mac_position = inputs["data:weight:aircraft:CG:aft:MAC_position"]
        cn_beta_fuselage = inputs["data:aerodynamics:fuselage:cruise:CnBeta"]
        cl_alpha_vt = inputs["data:aerodynamics:vertical_tail:cruise:CL_alpha"]
        cruise_mach = inputs["data:TLAR:cruise_mach"]
        # This one is the distance between the 25% MAC points
        wing_htp_distance = inputs["data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25"]

        # Matches suggested goal by Raymer, Fig 16.20
        cn_beta_goal = 0.0569 - 0.01694 * cruise_mach + 0.15904 * cruise_mach ** 2

        required_cnbeta_vtp = cn_beta_goal - cn_beta_fuselage
        distance_to_cg = wing_htp_distance + 0.25 * l0_wing - cg_mac_position * l0_wing
        vt_area = required_cnbeta_vtp / (distance_to_cg / wing_area / span * cl_alpha_vt)
        wet_vt_area = 2.1 * vt_area

        outputs["data:geometry:vertical_tail:wetted_area"] = wet_vt_area
        outputs["data:geometry:vertical_tail:area"] = vt_area
        outputs["data:aerodynamics:vertical_tail:cruise:CnBeta"] = required_cnbeta_vtp
