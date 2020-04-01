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

import numpy as np
from fastoad.models.aerodynamics.constants import POLAR_POINT_COUNT
from openmdao.core.explicitcomponent import ExplicitComponent


class ComputePolar(ExplicitComponent):
    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options["low_speed_aero"]

        self.add_input("tuning:aerodynamics:aircraft:cruise:CD:k", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CD:offset", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CD:winglet_effect:k", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CD:winglet_effect:offset", val=np.nan)

        nans_array = np.full(POLAR_POINT_COUNT, np.nan)
        if self.low_speed_aero:
            self.add_input("cl_low_speed", val=nans_array)
            self.add_input("cd0_total_low_speed", val=nans_array)
            self.add_input("cd_trim_low_speed", val=nans_array)
            self.add_input("cd_comp_low_speed", val=nans_array)
            self.add_input("oswald_coeff_low_speed", val=np.nan)

            self.add_output("aerodynamics:Cd_low_speed", shape=POLAR_POINT_COUNT)
        else:
            self.add_input("data:aerodynamics:aircraft:cruise:CL", val=nans_array)
            self.add_input("data:aerodynamics:aircraft:cruise:CD0", val=nans_array)
            self.add_input("data:aerodynamics:aircraft:cruise:CD:trim", val=nans_array)
            self.add_input("data:aerodynamics:aircraft:cruise:CD:compressibility", val=nans_array)
            self.add_input("data:aerodynamics:aircraft:cruise:induced_drag_coefficient", val=np.nan)

            self.add_output("data:aerodynamics:aircraft:cruise:CD", shape=POLAR_POINT_COUNT)
            self.add_output("data:aerodynamics:aircraft:cruise:L_D_max")
            self.add_output("data:aerodynamics:aircraft:cruise:optimal_CL")
            self.add_output("data:aerodynamics:aircraft:cruise:optimal_CD")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        k_cd = inputs["tuning:aerodynamics:aircraft:cruise:CD:k"]
        offset_cd = inputs["tuning:aerodynamics:aircraft:cruise:CD:offset"]
        k_winglet_cd = inputs["tuning:aerodynamics:aircraft:cruise:CD:winglet_effect:k"]
        offset_winglet_cd = inputs["tuning:aerodynamics:aircraft:cruise:CD:winglet_effect:offset"]
        if self.low_speed_aero:
            cl = inputs["cl_low_speed"]
            cd0 = inputs["cd0_total_low_speed"]
            cd_trim = inputs["cd_trim_low_speed"]
            cd_c = inputs["cd_comp_low_speed"]
            coef_k = inputs["oswald_coeff_low_speed"]
        else:
            cl = inputs["data:aerodynamics:aircraft:cruise:CL"]
            cd0 = inputs["data:aerodynamics:aircraft:cruise:CD0"]
            cd_trim = inputs["data:aerodynamics:aircraft:cruise:CD:trim"]
            cd_c = inputs["data:aerodynamics:aircraft:cruise:CD:compressibility"]
            coef_k = inputs["data:aerodynamics:aircraft:cruise:induced_drag_coefficient"]

        cd = (
            cd0 + cd_c + cd_trim + coef_k * cl ** 2 * k_winglet_cd + offset_winglet_cd
        ) * k_cd + offset_cd

        if self.low_speed_aero:
            outputs["aerodynamics:Cd_low_speed"] = cd
        else:
            outputs["data:aerodynamics:aircraft:cruise:CD"] = cd

            Cl_opt, Cd_opt = get_optimum_ClCd(np.array([cd, cl]))[0:2]
            outputs["data:aerodynamics:aircraft:cruise:L_D_max"] = Cl_opt / Cd_opt
            outputs["data:aerodynamics:aircraft:cruise:optimal_CL"] = Cl_opt
            outputs["data:aerodynamics:aircraft:cruise:optimal_CD"] = Cd_opt


def get_optimum_ClCd(ClCd):
    lift_drag_ratio = ClCd[1, :] / ClCd[0, :]
    optimum_index = np.argmax(lift_drag_ratio)

    optimum_Cz = ClCd[1][optimum_index]
    optimum_Cd = ClCd[0][optimum_index]

    return optimum_Cz, optimum_Cd
