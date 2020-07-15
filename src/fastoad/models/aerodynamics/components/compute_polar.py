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

from enum import Enum

import numpy as np
from fastoad.models.aerodynamics.constants import POLAR_POINT_COUNT
from openmdao.core.explicitcomponent import ExplicitComponent


class PolarType(Enum):
    HIGH_SPEED = "high_speed"
    LOW_SPEED = "low_speed"
    TAKEOFF = "takeoff"
    LANDING = "landing"


class ComputePolar(ExplicitComponent):
    def initialize(self):
        self.options.declare("type", default=PolarType.HIGH_SPEED, types=PolarType)

    def setup(self):
        self.add_input("tuning:aerodynamics:aircraft:cruise:CD:k", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CD:offset", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CD:winglet_effect:k", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CD:winglet_effect:offset", val=np.nan)

        nans_array = np.full(POLAR_POINT_COUNT, np.nan)
        if self.options["type"] != PolarType.HIGH_SPEED:
            self.add_input("data:aerodynamics:aircraft:low_speed:CL", val=nans_array)
            self.add_input("data:aerodynamics:aircraft:low_speed:CD0", val=nans_array)
            self.add_input("data:aerodynamics:aircraft:low_speed:CD:trim", val=nans_array)
            self.add_input(
                "data:aerodynamics:aircraft:low_speed:induced_drag_coefficient", val=np.nan
            )

            if self.options["type"] == PolarType.TAKEOFF:
                self.add_input("data:aerodynamics:high_lift_devices:takeoff:CL", val=np.nan)
                self.add_input("data:aerodynamics:high_lift_devices:takeoff:CD", val=np.nan)
                self.add_output("data:aerodynamics:aircraft:takeoff:CL", shape=POLAR_POINT_COUNT)
                self.add_output("data:aerodynamics:aircraft:takeoff:CD", shape=POLAR_POINT_COUNT)

            elif self.options["type"] == PolarType.LANDING:
                self.add_input("data:aerodynamics:high_lift_devices:landing:CL", val=np.nan)
                self.add_input("data:aerodynamics:high_lift_devices:landing:CD", val=np.nan)
                self.add_output("data:aerodynamics:landing:CL", val=np.nan)
                self.add_output("data:aerodynamics:aircraft:landing:CL", shape=POLAR_POINT_COUNT)
                self.add_output("data:aerodynamics:aircraft:landing:CD", shape=POLAR_POINT_COUNT)
            else:
                self.add_output("data:aerodynamics:aircraft:low_speed:CD", shape=POLAR_POINT_COUNT)

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
        if self.options["type"] != PolarType.HIGH_SPEED:
            cl = inputs["data:aerodynamics:aircraft:low_speed:CL"]
            cd0 = inputs["data:aerodynamics:aircraft:low_speed:CD0"]
            cd_trim = inputs["data:aerodynamics:aircraft:low_speed:CD:trim"]
            cd_c = 0.0
            coef_k = inputs["data:aerodynamics:aircraft:low_speed:induced_drag_coefficient"]
            if self.options["type"] == PolarType.TAKEOFF:
                delta_cl_hl = inputs["data:aerodynamics:high_lift_devices:takeoff:CL"]
                delta_cd_hl = inputs["data:aerodynamics:high_lift_devices:takeoff:CD"]
            elif self.options["type"] == PolarType.LANDING:
                delta_cl_hl = inputs["data:aerodynamics:high_lift_devices:landing:CL"]
                delta_cd_hl = inputs["data:aerodynamics:high_lift_devices:landing:CD"]
            else:
                delta_cl_hl = 0.0
                delta_cd_hl = 0.0

        else:
            cl = inputs["data:aerodynamics:aircraft:cruise:CL"]
            cd0 = inputs["data:aerodynamics:aircraft:cruise:CD0"]
            cd_trim = inputs["data:aerodynamics:aircraft:cruise:CD:trim"]
            cd_c = inputs["data:aerodynamics:aircraft:cruise:CD:compressibility"]
            coef_k = inputs["data:aerodynamics:aircraft:cruise:induced_drag_coefficient"]
            delta_cl_hl = 0.0
            delta_cd_hl = 0.0

        cl = cl + delta_cl_hl
        cd = (
            cd0 + cd_c + cd_trim + coef_k * cl ** 2 * k_winglet_cd + offset_winglet_cd + delta_cd_hl
        ) * k_cd + offset_cd

        if self.options["type"] == PolarType.LOW_SPEED:
            outputs["data:aerodynamics:aircraft:low_speed:CD"] = cd
        elif self.options["type"] == PolarType.TAKEOFF:
            outputs["data:aerodynamics:aircraft:takeoff:CL"] = cl
            outputs["data:aerodynamics:aircraft:takeoff:CD"] = cd
        elif self.options["type"] == PolarType.LANDING:
            outputs["data:aerodynamics:aircraft:landing:CL"] = cl
            outputs["data:aerodynamics:aircraft:landing:CD"] = cd
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
