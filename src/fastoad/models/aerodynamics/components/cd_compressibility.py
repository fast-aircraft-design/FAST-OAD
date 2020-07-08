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
from fastoad.models.aerodynamics.constants import POLAR_POINT_COUNT
from openmdao.core.explicitcomponent import ExplicitComponent


class CdCompressibility(ExplicitComponent):
    def setup(self):

        nans_array = np.full(POLAR_POINT_COUNT, np.nan)
        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:CL", val=nans_array)
        self.add_output(
            "data:aerodynamics:aircraft:cruise:CD:compressibility", shape=POLAR_POINT_COUNT
        )

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        cl = inputs["data:aerodynamics:aircraft:cruise:CL"]
        m = inputs["data:TLAR:cruise_mach"]

        cd_comp = []

        for cl_val in cl:
            # FIXME: The computed characteristic Mach is for sweep angle 28° and relative thickness
            #        of 0.12. It should be corrected according to actual values
            m_charac_comp = -0.5 * max(0.35, cl_val) ** 2 + 0.35 * max(0.35, cl_val) + 0.765
            cd_comp.append(0.002 * exp(42.58 * (m - m_charac_comp)))

        outputs["data:aerodynamics:aircraft:cruise:CD:compressibility"] = cd_comp
