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


class Cd0Total(ExplicitComponent):
    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options["low_speed_aero"]

        self.add_input("data:geometry:aircraft:wetted_area", val=np.nan, units="m**2")

        nans_array = np.full(POLAR_POINT_COUNT, np.nan)
        if self.low_speed_aero:
            self.add_input("cd0_wing_low_speed", val=nans_array)
            self.add_input("cd0_fuselage_low_speed", val=nans_array)
            self.add_input("cd0_ht_low_speed", val=np.nan)
            self.add_input("cd0_vt_low_speed", val=np.nan)
            self.add_input("cd0_nacelle_low_speed", val=np.nan)
            self.add_input("cd0_pylon_low_speed", val=np.nan)
            self.add_output("cd0_total_low_speed", shape=POLAR_POINT_COUNT)
        else:
            self.add_input("data:aerodynamics:wing:cruise:CD0", val=nans_array)
            self.add_input("data:aerodynamics:fuselage:cruise:CD0", val=nans_array)
            self.add_input("data:aerodynamics:horizontal_tail:cruise:CD0", val=np.nan)
            self.add_input("data:aerodynamics:vertical_tail:cruise:CD0", val=np.nan)
            self.add_input("data:aerodynamics:nacelles:cruise:CD0", val=np.nan)
            self.add_input("data:aerodynamics:pylons:cruise:CD0", val=np.nan)
            self.add_output("data:aerodynamics:aircraft:cruise:CD0", shape=POLAR_POINT_COUNT)

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        wet_area_total = inputs["data:geometry:aircraft:wetted_area"]
        if self.low_speed_aero:
            cd0_wing = inputs["cd0_wing_low_speed"]
            cd0_fus = inputs["cd0_fuselage_low_speed"]
            cd0_ht = inputs["cd0_ht_low_speed"]
            cd0_vt = inputs["cd0_vt_low_speed"]
            cd0_nac = inputs["cd0_nacelle_low_speed"]
            cd0_pylon = inputs["cd0_pylon_low_speed"]
        else:
            cd0_wing = inputs["data:aerodynamics:wing:cruise:CD0"]
            cd0_fus = inputs["data:aerodynamics:fuselage:cruise:CD0"]
            cd0_ht = inputs["data:aerodynamics:horizontal_tail:cruise:CD0"]
            cd0_vt = inputs["data:aerodynamics:vertical_tail:cruise:CD0"]
            cd0_nac = inputs["data:aerodynamics:nacelles:cruise:CD0"]
            cd0_pylon = inputs["data:aerodynamics:pylons:cruise:CD0"]

        k_techno = 1
        k_parasite = (
            -2.39 * pow(10, -12) * wet_area_total ** 3
            + 2.58 * pow(10, -8) * wet_area_total ** 2
            - 0.89 * pow(10, -4) * wet_area_total
            + 0.163
        )

        cd0_total_hs = cd0_wing + cd0_fus + cd0_ht + cd0_vt + cd0_nac + cd0_pylon
        cd0_total = cd0_total_hs * (1.0 + k_parasite * k_techno)

        if self.low_speed_aero:
            outputs["cd0_total_low_speed"] = cd0_total
        else:
            outputs["data:aerodynamics:aircraft:cruise:CD0"] = cd0_total
