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


class CdTrim(ExplicitComponent):
    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options["low_speed_aero"]

        nans_array = np.full(POLAR_POINT_COUNT, np.nan)
        if self.low_speed_aero:
            self.add_input("data:aerodynamics:aircraft:low_speed:CL", val=nans_array)
            self.add_output("data:aerodynamics:aircraft:low_speed:CD:trim", shape=POLAR_POINT_COUNT)
        else:
            self.add_input("data:aerodynamics:aircraft:cruise:CL", val=nans_array)
            self.add_output("data:aerodynamics:aircraft:cruise:CD:trim", shape=POLAR_POINT_COUNT)

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        if self.low_speed_aero:
            cl = inputs["data:aerodynamics:aircraft:low_speed:CL"]
        else:
            cl = inputs["data:aerodynamics:aircraft:cruise:CL"]

        cd_trim = []

        for cl_val in cl:
            cd_trim.append(5.89 * pow(10, -4) * cl_val)

        if self.low_speed_aero:
            outputs["data:aerodynamics:aircraft:low_speed:CD:trim"] = cd_trim
        else:
            outputs["data:aerodynamics:aircraft:cruise:CD:trim"] = cd_trim
