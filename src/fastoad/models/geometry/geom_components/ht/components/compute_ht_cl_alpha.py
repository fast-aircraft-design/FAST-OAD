"""
    Estimation of horizontal tail lift coefficient
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
class ComputeHTClalpha(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Horizontal tail lift coefficient estimation"""

    def setup(self):
        self.add_input("data:geometry:horizontal_tail:aspect_ratio", val=np.nan)
        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:sweep_25", val=np.nan, units="deg")

        self.add_output("data:aerodynamics:horizontal_tail:cruise:CL_alpha")

    def setup_partials(self):
        self.declare_partials("data:aerodynamics:horizontal_tail:cruise:CL_alpha", "*", method="fd")

    def compute(self, inputs, outputs):
        cruise_mach = inputs["data:TLAR:cruise_mach"]
        lambda_ht = inputs["data:geometry:horizontal_tail:aspect_ratio"]
        sweep_25_ht = inputs["data:geometry:horizontal_tail:sweep_25"]

        beta = math.sqrt(1 - cruise_mach ** 2)
        cl_alpha_ht = (
            0.8
            * 2
            * math.pi
            * lambda_ht
            / (
                2
                + math.sqrt(
                    4
                    + lambda_ht ** 2
                    * beta ** 2
                    / 0.95 ** 2
                    * (1 + (math.tan(sweep_25_ht / 180.0 * math.pi)) ** 2 / beta ** 2)
                )
            )
        )

        outputs["data:aerodynamics:horizontal_tail:cruise:CL_alpha"] = cl_alpha_ht
