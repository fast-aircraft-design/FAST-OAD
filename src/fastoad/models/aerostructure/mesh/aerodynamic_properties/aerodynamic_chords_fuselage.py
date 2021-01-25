"""
Computes Aerodynamic fuselage mesh sections length
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

import openmdao.api as om
import numpy as np


class AerodynamicChordsFuselage(om.ExplicitComponent):
    """
    Computes fuselage chords length for each aerodynamic section
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int, allow_none=True)

    def setup(self):
        self.add_input("data:geometry:fuselage:length", val=np.nan)
        self.add_input("data:geometry:fuselage:front_length", val=np.nan)
        self.add_input("data:geometry:fuselage:rear_length", val=np.nan)

        self.add_output("data:aerostructural:aerodynamic:fuselage:chords", shape=(12, 1))

    def setup_partials(self):
        self.declare_partials("*", "*", "fd")

    def compute(self, inputs, outputs):
        c_h_right = np.zeros(3)
        c_v_top = np.zeros(3)
        c_v_bottom = np.zeros(3)
        c_h_right[0] = inputs["data:geometry:fuselage:length"][0]
        c_h_right[1] = (
            inputs["data:geometry:fuselage:length"][0]
            - inputs["data:geometry:fuselage:rear_length"][0] / 2
        )
        c_h_right[2] = (
            inputs["data:geometry:fuselage:length"][0]
            - inputs["data:geometry:fuselage:front_length"][0]
            - inputs["data:geometry:fuselage:rear_length"][0]
        )
        c_v_top[0] = inputs["data:geometry:fuselage:length"][0]
        c_v_top[1] = inputs["data:geometry:fuselage:length"][0]
        c_v_top[2] = (
            inputs["data:geometry:fuselage:length"][0]
            - inputs["data:geometry:fuselage:front_length"][0]
        )
        c_v_bottom[0] = inputs["data:geometry:fuselage:length"][0]
        c_v_bottom[1] = (
            inputs["data:geometry:fuselage:length"][0]
            - inputs["data:geometry:fuselage:rear_length"][0] / 2
        )
        c_v_bottom[2] = (
            inputs["data:geometry:fuselage:length"][0]
            - inputs["data:geometry:fuselage:front_length"][0]
            - inputs["data:geometry:fuselage:rear_length"][0]
        )
        chords = np.vstack((c_h_right, c_h_right, c_v_top, c_v_bottom))
        outputs["data:aerostructural:aerodynamic:fuselage:chords"] = chords
