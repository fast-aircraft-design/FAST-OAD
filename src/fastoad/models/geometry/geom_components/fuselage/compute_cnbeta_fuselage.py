"""
    Estimation of yawing moment due to sideslip
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

import fastoad.api as oad
from ...constants import SERVICE_FUSELAGE_CNBETA


# TODO: This belongs more to aerodynamics than geometry
@oad.RegisterSubmodel(SERVICE_FUSELAGE_CNBETA, "fastoad.submodel.geometry.fuselage.cnbeta.legacy")
class ComputeCnBetaFuselage(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Yawing moment due to sideslip estimation"""

    def setup(self):
        self.add_input("data:geometry:fuselage:maximum_width", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:length", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:front_length", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:rear_length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")

        self.add_output("data:aerodynamics:fuselage:cruise:CnBeta")

    def setup_partials(self):
        self.declare_partials("data:aerodynamics:fuselage:cruise:CnBeta", "*", method="fd")

    def compute(self, inputs, outputs):
        fus_length = inputs["data:geometry:fuselage:length"]
        lav = inputs["data:geometry:fuselage:front_length"]
        lar = inputs["data:geometry:fuselage:rear_length"]
        width_max = inputs["data:geometry:fuselage:maximum_width"]
        height_max = inputs["data:geometry:fuselage:maximum_height"]
        wing_area = inputs["data:geometry:wing:area"]
        span = inputs["data:geometry:wing:span"]

        l_f = math.sqrt(width_max * height_max)
        l_cyc = fus_length - lav - lar
        # estimation of fuselage volume
        volume_fus = math.pi * l_f ** 2 / 4 * (0.7 * lav + 0.5 * lar + l_cyc)
        # equation from raymer book eqn. 16.47
        cn_beta_fus = -1.3 * volume_fus / wing_area / span * (l_f / width_max)

        outputs["data:aerodynamics:fuselage:cruise:CnBeta"] = cn_beta_fus
