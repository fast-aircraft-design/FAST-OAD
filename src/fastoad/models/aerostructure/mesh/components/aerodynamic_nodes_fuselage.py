"""
Computes Aerodynamic mesh nodes locations
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


class AerodynamicNodesFuselage(om.ExplicitComponent):
    """
    Computes horizontal tail points for aerodynamic grid generation (AVL)
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int, allow_none=True)

    def setup(self):
        # Declare inputs ---------------------------------------------------------------------------
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan)
        self.add_input("data:geometry:fuselage:maximum_width", val=np.nan)
        self.add_input("data:geometry:fuselage:front_length", val=np.nan)
        # Declare outputs --------------------------------------------------------------------------

        self.add_output("data:aerostructural:aerodynamic:fuselage:nodes", val=np.nan, shape=(12, 3))

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        # Prepare inputs ---------------------------------------------------------------------------
        xyz_h_right = np.zeros((3, 3))
        xyz_h_left = np.zeros((3, 3))
        xyz_v_top = np.zeros((3, 3))
        xyz_v_bottom = np.zeros((3, 3))

        xyz_h_right[1, 1] = inputs["data:geometry:fuselage:maximum_width"][0] / 4
        xyz_h_right[2, 0] = inputs["data:geometry:fuselage:front_length"][0]
        xyz_h_right[2, 1] = inputs["data:geometry:fuselage:maximum_width"][0] / 2
        xyz_h_left[1, 1] = -inputs["data:geometry:fuselage:maximum_width"][0] / 4
        xyz_h_left[2, 0] = inputs["data:geometry:fuselage:front_length"][0]
        xyz_h_left[2, 1] = -inputs["data:geometry:fuselage:maximum_width"][0] / 2

        xyz_v_top[1, 2] = inputs["data:geometry:fuselage:maximum_height"][0] / 4
        xyz_v_top[2, 0] = inputs["data:geometry:fuselage:front_length"][0]
        xyz_v_top[2, 2] = inputs["data:geometry:fuselage:maximum_height"][0] / 2
        xyz_v_bottom[1, 2] = -inputs["data:geometry:fuselage:maximum_height"][0] / 4
        xyz_v_bottom[2, 0] = inputs["data:geometry:fuselage:front_length"][0]
        xyz_v_bottom[2, 2] = -inputs["data:geometry:fuselage:maximum_height"][0] / 2

        outputs["data:aerostructural:aerodynamic:fuselage:nodes"] = np.vstack(
            (xyz_h_right, xyz_h_left, xyz_v_top, xyz_v_bottom)
        )
