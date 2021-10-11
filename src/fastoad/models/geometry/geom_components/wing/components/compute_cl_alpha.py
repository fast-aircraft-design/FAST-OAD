"""
    Estimation of wing lift coefficient
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
class ComputeCLalpha(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Wing lift coefficient estimation"""

    def setup(self):
        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:geometry:fuselage:maximum_width", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan, units="m")
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:wing:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:thickness_ratio", val=np.nan)
        self.add_input("data:geometry:wing:sweep_25", val=np.nan, units="deg")
        self.add_input("data:geometry:wing:aspect_ratio", val=np.nan)
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")

        self.add_output("data:aerodynamics:aircraft:cruise:CL_alpha")

    def setup_partials(self):
        self.declare_partials("data:aerodynamics:aircraft:cruise:CL_alpha", "*", method="fd")

    def compute(self, inputs, outputs):
        cruise_mach = inputs["data:TLAR:cruise_mach"]
        width_max = inputs["data:geometry:fuselage:maximum_width"]
        height_max = inputs["data:geometry:fuselage:maximum_height"]
        span = inputs["data:geometry:wing:span"]
        lambda_wing = inputs["data:geometry:wing:aspect_ratio"]
        el_ext = inputs["data:geometry:wing:tip:thickness_ratio"]
        wing_area = inputs["data:geometry:wing:area"]
        l2_wing = inputs["data:geometry:wing:root:chord"]
        l4_wing = inputs["data:geometry:wing:tip:chord"]
        sweep_25 = inputs["data:geometry:wing:sweep_25"]

        beta = math.sqrt(1 - cruise_mach ** 2)
        d_f = math.sqrt(width_max * height_max)
        fact_f = 1.07 * (1 + d_f / span) ** 2
        lambda_wing_eff = lambda_wing * (1 + 1.9 * l4_wing * el_ext / span)
        cl_alpha_wing = (
            2
            * math.pi
            * lambda_wing_eff
            / (
                2
                + math.sqrt(
                    4
                    + lambda_wing_eff ** 2
                    * beta ** 2
                    / 0.95 ** 2
                    * (1 + (math.tan(sweep_25 / 180.0 * math.pi)) ** 2 / beta ** 2)
                )
            )
            * (wing_area - l2_wing * width_max)
            / wing_area
            * fact_f
        )

        outputs["data:aerodynamics:aircraft:cruise:CL_alpha"] = cl_alpha_wing
