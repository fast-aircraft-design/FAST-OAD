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

import math

import numpy as np
from fastoad.models.aerodynamics.constants import POLAR_POINT_COUNT
from openmdao.core.explicitcomponent import ExplicitComponent


class Cd0Fuselage(ExplicitComponent):
    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options["low_speed_aero"]
        nans_array = np.full(POLAR_POINT_COUNT, np.nan)
        if self.low_speed_aero:
            self.add_input("data:aerodynamics:wing:low_speed:reynolds", val=np.nan)
            self.add_input("data:aerodynamics:aircraft:low_speed:CL", val=nans_array)
            self.add_input("data:aerodynamics:aircraft:takeoff:mach", val=np.nan)
            self.add_output("data:aerodynamics:fuselage:low_speed:CD0", shape=POLAR_POINT_COUNT)
        else:
            self.add_input("data:aerodynamics:wing:cruise:reynolds", val=np.nan)
            self.add_input("data:aerodynamics:aircraft:cruise:CL", val=nans_array)
            self.add_input("data:TLAR:cruise_mach", val=np.nan)
            self.add_output("data:aerodynamics:fuselage:cruise:CD0", shape=POLAR_POINT_COUNT)

        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:fuselage:length", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_width", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:wetted_area", val=np.nan, units="m**2")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        height_max = inputs["data:geometry:fuselage:maximum_height"]
        width_max = inputs["data:geometry:fuselage:maximum_width"]
        wet_area_fus = inputs["data:geometry:fuselage:wetted_area"]
        wing_area = inputs["data:geometry:wing:area"]
        fus_length = inputs["data:geometry:fuselage:length"]
        if self.low_speed_aero:
            cl = inputs["data:aerodynamics:aircraft:low_speed:CL"]
            mach = inputs["data:aerodynamics:aircraft:takeoff:mach"]
            reynolds = inputs["data:aerodynamics:wing:low_speed:reynolds"]
        else:
            cl = inputs["data:aerodynamics:aircraft:cruise:CL"]
            mach = inputs["data:TLAR:cruise_mach"]
            reynolds = inputs["data:aerodynamics:wing:cruise:reynolds"]

        cf_fus = 0.455 / (
            (1 + 0.144 * mach ** 2) ** 0.65 * (math.log10(reynolds * fus_length)) ** 2.58
        )

        cd0_friction_fus = (
            (0.98 + 0.745 * math.sqrt(height_max * width_max) / fus_length)
            * cf_fus
            * wet_area_fus
            / wing_area
        )
        cd0_upsweep_fus = (
            (0.0029 * cl ** 2 - 0.0066 * cl + 0.0043)
            * (0.67 * 3.6 * height_max * width_max)
            / wing_area
        )
        cd0_fus = cd0_friction_fus + cd0_upsweep_fus

        if self.low_speed_aero:
            outputs["data:aerodynamics:fuselage:low_speed:CD0"] = cd0_fus
        else:
            outputs["data:aerodynamics:fuselage:cruise:CD0"] = cd0_fus
