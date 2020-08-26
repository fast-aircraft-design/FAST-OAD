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
from fastoad.utils.physics import AtmosphereSI
from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeReynolds(ExplicitComponent):
    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options["low_speed_aero"]

        if self.low_speed_aero:
            self.add_input("data:aerodynamics:aircraft:takeoff:mach", val=np.nan)
            self.add_output("data:aerodynamics:wing:low_speed:reynolds")
        else:
            self.add_input("data:TLAR:cruise_mach", val=np.nan)
            self.add_input("data:mission:sizing:main_route:cruise:altitude", val=np.nan, units="m")
            self.add_output("data:aerodynamics:wing:cruise:reynolds")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        if self.low_speed_aero:
            mach = inputs["data:aerodynamics:aircraft:takeoff:mach"]
            altitude = 0.0
        else:
            mach = inputs["data:TLAR:cruise_mach"]
            altitude = inputs["data:mission:sizing:main_route:cruise:altitude"]

        reynolds = AtmosphereSI(altitude).get_unitary_reynolds(mach)

        if self.low_speed_aero:
            outputs["data:aerodynamics:wing:low_speed:reynolds"] = reynolds
        else:
            outputs["data:aerodynamics:wing:cruise:reynolds"] = reynolds
