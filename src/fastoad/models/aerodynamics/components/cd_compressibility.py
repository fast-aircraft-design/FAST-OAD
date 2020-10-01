"""
    FAST - Copyright (c) 2016 ONERA ISAE
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

from math import exp

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class CdCompressibility(ExplicitComponent):
    """
    Computation of drag increment due to compressibility effects.

    Formula from §4.2.4 of :cite:`supaero:2014`.
    """

    def setup(self):

        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:CL", shape_by_conn=True, val=np.nan)
        self.add_input("data:geometry:wing:sweep_25", units="deg", val=np.nan)
        self.add_input("data:geometry:wing:thickness_ratio", val=np.nan)
        self.add_output(
            "data:aerodynamics:aircraft:cruise:CD:compressibility",
            copy_shape="data:aerodynamics:aircraft:cruise:CL",
        )

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        cl = inputs["data:aerodynamics:aircraft:cruise:CL"]
        m = inputs["data:TLAR:cruise_mach"]

        sweep_angle = inputs["data:geometry:wing:sweep_25"]
        thickness_ratio = inputs["data:geometry:wing:thickness_ratio"]

        cd_comp = []

        for cl_val in cl:
            # Computation of characteristic Mach for 28° sweep and 0.12 of relative thickness
            m_charac_comp_0 = -0.5 * max(0.35, cl_val) ** 2 + 0.35 * max(0.35, cl_val) + 0.765

            # Computation of characteristic Mach for actual sweep angle and relative thickness
            m_charac_comp = (
                m_charac_comp_0 * np.cos(np.radians(28)) + 0.12 - thickness_ratio
            ) / np.cos(np.radians(sweep_angle))

            cd_comp.append(0.002 * exp(42.58 * (m - m_charac_comp)))

        outputs["data:aerodynamics:aircraft:cruise:CD:compressibility"] = cd_comp
