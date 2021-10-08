"""Computation of CL characteristics at low speed."""
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
from ..constants import SERVICE_LOW_SPEED_CL_AOA


@RegisterSubmodel(SERVICE_LOW_SPEED_CL_AOA, "fastoad.submodel.aerodynamics.low_speed.AoA.legacy")
class ComputeAerodynamicsLowSpeed(om.ExplicitComponent):
    """
    Computes CL gradient and CL at low speed.

    CL gradient from :cite:`raymer:1999` Eq 12.6
    """

    # TODO: complete source

    def setup(self):
        self.add_input("data:geometry:fuselage:maximum_width", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan, units="m")
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")
        self.add_input("data:geometry:wing:aspect_ratio", val=np.nan)
        self.add_input("data:geometry:wing:tip:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:sweep_25", val=np.nan, units="deg")
        self.add_input("data:geometry:wing:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:wing:tip:thickness_ratio", val=np.nan)

        self.add_output("data:aerodynamics:aircraft:takeoff:CL_alpha", units="1/rad")
        self.add_output("data:aerodynamics:aircraft:takeoff:CL0_clean")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        width_max = inputs["data:geometry:fuselage:maximum_width"]
        height_max = inputs["data:geometry:fuselage:maximum_height"]
        span = inputs["data:geometry:wing:span"]
        lambda_wing = inputs["data:geometry:wing:aspect_ratio"]
        l2_wing = inputs["data:geometry:wing:root:chord"]
        l4_wing = inputs["data:geometry:wing:tip:chord"]
        el_ext = inputs["data:geometry:wing:tip:thickness_ratio"]
        sweep_25 = inputs["data:geometry:wing:sweep_25"]
        wing_area = inputs["data:geometry:wing:area"]

        mach = 0.2

        beta = np.sqrt(1 - mach ** 2)
        d_f = np.sqrt(width_max * height_max)
        fuselage_lift_factor = 1.07 * (1 + d_f / span) ** 2
        lambda_wing_eff = lambda_wing * (1 + 1.9 * l4_wing * el_ext / span)
        cl_alpha_wing_low = (
            2
            * np.pi
            * lambda_wing_eff
            / (
                2
                + np.sqrt(
                    4
                    + lambda_wing_eff ** 2
                    * beta ** 2
                    / 0.95 ** 2
                    * (1 + (np.tan(sweep_25 / 180.0 * np.pi)) ** 2 / beta ** 2)
                )
            )
            * (wing_area - l2_wing * width_max)
            / wing_area
            * fuselage_lift_factor
        )

        outputs["data:aerodynamics:aircraft:takeoff:CL_alpha"] = cl_alpha_wing_low
        outputs["data:aerodynamics:aircraft:takeoff:CL0_clean"] = 0.2  # FIXME: hard-coded value
