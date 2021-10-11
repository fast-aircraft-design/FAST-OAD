"""
Computation of Oswald coefficient
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
from ..constants import SERVICE_INDUCED_DRAG_COEFFICIENT, SERVICE_OSWALD_COEFFICIENT


@RegisterSubmodel(
    SERVICE_INDUCED_DRAG_COEFFICIENT,
    "fastoad.submodel.aerodynamics.induced_drag_coefficient.legacy",
)
class InducedDragCoefficient(om.ExplicitComponent):
    """Computes the coefficient that should be multiplied by CL**2 to get induced drag."""

    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")

        if self.options["low_speed_aero"]:
            self.add_input("data:aerodynamics:aircraft:low_speed:oswald_coefficient", val=np.nan)
            self.add_output("data:aerodynamics:aircraft:low_speed:induced_drag_coefficient")
        else:
            self.add_input("data:aerodynamics:aircraft:cruise:oswald_coefficient", val=np.nan)
            self.add_output("data:aerodynamics:aircraft:cruise:induced_drag_coefficient")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        wing_area = inputs["data:geometry:wing:area"]
        span = inputs["data:geometry:wing:span"] / np.cos(5.0 / 180 * np.pi)
        aspect_ratio = span ** 2 / wing_area

        if self.options["low_speed_aero"]:
            coef_e = inputs["data:aerodynamics:aircraft:low_speed:oswald_coefficient"]
        else:
            coef_e = inputs["data:aerodynamics:aircraft:cruise:oswald_coefficient"]

        coef_k = 1.0 / (np.pi * aspect_ratio * coef_e)

        if self.options["low_speed_aero"]:
            outputs["data:aerodynamics:aircraft:low_speed:induced_drag_coefficient"] = coef_k
        else:
            outputs["data:aerodynamics:aircraft:cruise:induced_drag_coefficient"] = coef_k


@RegisterSubmodel(
    SERVICE_OSWALD_COEFFICIENT, "fastoad.submodel.aerodynamics.oswald_coefficient.legacy"
)
class OswaldCoefficient(om.ExplicitComponent):
    """Computes Oswald efficiency number"""

    # TODO: Document equations. Cite sources (M. Nita and D. Scholz)

    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_width", val=np.nan, units="m")
        self.add_input("data:geometry:wing:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:sweep_25", val=np.nan, units="deg")

        if self.options["low_speed_aero"]:
            self.add_input("data:aerodynamics:aircraft:takeoff:mach", val=np.nan)
            self.add_output("data:aerodynamics:aircraft:low_speed:oswald_coefficient")
        else:
            self.add_input("data:TLAR:cruise_mach", val=np.nan)
            self.add_output("data:aerodynamics:aircraft:cruise:oswald_coefficient")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        wing_area = inputs["data:geometry:wing:area"]
        span = inputs["data:geometry:wing:span"] / np.cos(5.0 / 180 * np.pi)
        height_fus = inputs["data:geometry:fuselage:maximum_height"]
        width_fus = inputs["data:geometry:fuselage:maximum_width"]
        l2_wing = inputs["data:geometry:wing:root:chord"]
        l4_wing = inputs["data:geometry:wing:tip:chord"]
        sweep_25 = inputs["data:geometry:wing:sweep_25"]
        if self.options["low_speed_aero"]:
            mach = inputs["data:aerodynamics:aircraft:takeoff:mach"]
        else:
            mach = inputs["data:TLAR:cruise_mach"]

        aspect_ratio = span ** 2 / wing_area
        df = np.sqrt(width_fus * height_fus)
        lamda = l4_wing / l2_wing
        delta_lamda = -0.357 + 0.45 * np.exp(0.0375 * sweep_25 / 180.0 * np.pi)
        lamda = lamda - delta_lamda
        f_lamda = (
            0.0524 * lamda ** 4 - 0.15 * lamda ** 3 + 0.1659 * lamda ** 2 - 0.0706 * lamda + 0.0119
        )
        e_theory = 1 / (1 + f_lamda * aspect_ratio)

        if mach <= 0.4:
            ke_m = 1.0
        else:
            ke_m = -0.001521 * ((mach - 0.05) / 0.3 - 1) ** 10.82 + 1

        ke_f = 1 - 2 * (df / span) ** 2
        coef_e = e_theory * ke_f * ke_m * 0.9

        if self.options["low_speed_aero"]:
            outputs["data:aerodynamics:aircraft:low_speed:oswald_coefficient"] = coef_e
        else:
            outputs["data:aerodynamics:aircraft:cruise:oswald_coefficient"] = coef_e
