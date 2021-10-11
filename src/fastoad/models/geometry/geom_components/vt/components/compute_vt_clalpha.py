"""
    Estimation of vertical tail lift coefficient
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


# TODO: This belongs more to aerodynamics than geometry


class ComputeVTClalpha(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Vertical tail lift coefficient estimation"""

    def setup(self):
        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:geometry:has_T_tail", val=np.nan)
        self.add_input("data:geometry:vertical_tail:aspect_ratio", val=np.nan)
        self.add_input("data:geometry:vertical_tail:sweep_25", val=np.nan, units="deg")

        self.add_output("data:aerodynamics:vertical_tail:cruise:CL_alpha")

    def setup_partials(self):
        self.declare_partials("data:aerodynamics:vertical_tail:cruise:CL_alpha", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        tail_type = np.round(inputs["data:geometry:has_T_tail"])
        cruise_mach = inputs["data:TLAR:cruise_mach"]
        sweep_25_vt = inputs["data:geometry:vertical_tail:sweep_25"]
        k_ar_effective = 2.9 if tail_type == 1 else 1.55
        lambda_vt = inputs["data:geometry:vertical_tail:aspect_ratio"] * k_ar_effective

        beta = math.sqrt(1 - cruise_mach ** 2)
        cl_alpha_vt = (
            0.8
            * 2
            * math.pi
            * lambda_vt
            / (
                2
                + math.sqrt(
                    4
                    + lambda_vt ** 2
                    * beta ** 2
                    / 0.95 ** 2
                    * (1 + (math.tan(sweep_25_vt / 180.0 * math.pi)) ** 2 / beta ** 2)
                )
            )
        )

        outputs["data:aerodynamics:vertical_tail:cruise:CL_alpha"] = cl_alpha_vt
