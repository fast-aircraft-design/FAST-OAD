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


class InitializeClPolar(ExplicitComponent):
    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options["low_speed_aero"]

        self.add_input("tuning:aerodynamics:aircraft:cruise:CL:k", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CL:offset", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CL:winglet_effect:k", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CL:winglet_effect:offset", val=np.nan)

        if self.low_speed_aero:
            self.add_output("data:aerodynamics:aircraft:low_speed:CL", shape=POLAR_POINT_COUNT)
        else:
            self.add_output("data:aerodynamics:aircraft:cruise:CL", shape=POLAR_POINT_COUNT)

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        k_cl = inputs["tuning:aerodynamics:aircraft:cruise:CL:k"]
        offset_cl = inputs["tuning:aerodynamics:aircraft:cruise:CL:offset"]
        k_winglet_cl = inputs["tuning:aerodynamics:aircraft:cruise:CL:winglet_effect:k"]
        offset_winglet_cl = inputs["tuning:aerodynamics:aircraft:cruise:CL:winglet_effect:offset"]

        # FIXME: initialization of CL range should be done more directly, without these coefficients
        cl = np.arange(0.0, 1.5, 0.01) * k_cl * k_winglet_cl + offset_cl + offset_winglet_cl

        if self.low_speed_aero:
            outputs["data:aerodynamics:aircraft:low_speed:CL"] = cl
        else:
            outputs["data:aerodynamics:aircraft:cruise:CL"] = cl
