"""
This module computes structure nodes coordinates for wings
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
from scipy.interpolate import interp1d as interp


class StructureNodesWing(om.ExplicitComponent):
    """
    This Class compute wing structure nodes coordinates based on "number_of_sections" options value
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]
        self.add_input("data:geometry:wing:span", val=np.nan)
        self.add_input("data:geometry:wing:root:y", val=np.nan)
        self.add_input("data:geometry:wing:root:z", val=0.0)
        self.add_input("data:geometry:wing:root:chord", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:front:root", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:rear:root", val=np.nan)
        self.add_input("data:geometry:wing:kink:leading_edge:x:local", val=np.nan)
        self.add_input("data:geometry:wing:kink:y", val=np.nan)
        self.add_input("data:geometry:wing:kink:z", val=0.0)
        self.add_input("data:geometry:wing:kink:chord", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:front:kink", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:rear:kink", val=np.nan)
        self.add_input("data:geometry:wing:tip:leading_edge:x:local", val=np.nan)
        self.add_input("data:geometry:wing:tip:y", val=np.nan)
        self.add_input("data:geometry:wing:tip:z", val=0.0)
        self.add_input("data:geometry:wing:tip:chord", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:front:tip", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:rear:tip", val=np.nan)
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:geometry:wing:MAC:length", val=np.nan)
        self.add_input("data:geometry:wing:MAC:leading_edge:x:local", val=np.nan)
        # self.add_input("settings:aerostructural:wing:struct_sections", val=np.nan)
        self.add_output(
            "data:aerostructural:structure:wing:nodes", val=np.nan, shape=((n_secs + 1) * 2, 3)
        )

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]

        #  Characteristic points -------------------------------------------------------------------
        x_root = (
            inputs["data:geometry:wing:MAC:at25percent:x"][0]
            - 0.25 * inputs["data:geometry:wing:MAC:length"][0]
            - inputs["data:geometry:wing:MAC:leading_edge:x:local"][0]
        )
        x_kink = x_root + inputs["data:geometry:wing:kink:leading_edge:x:local"][0]
        x_tip = x_root + inputs["data:geometry:wing:tip:leading_edge:x:local"][0]
        y_root = inputs["data:geometry:wing:root:y"][0]
        y_wing = 0.5 * inputs["data:geometry:wing:span"][0] - y_root
        y_kink = inputs["data:geometry:wing:kink:y"][0]
        y_tip = inputs["data:geometry:wing:tip:y"][0]
        z_root = inputs["data:geometry:wing:root:z"][0]
        z_kink = inputs["data:geometry:wing:kink:z"][0]
        z_tip = inputs["data:geometry:wing:tip:z"][0]
        root_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:root"][0]
        root_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:root"][0]
        kink_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:kink"][0]
        kink_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:kink"][0]
        tip_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:tip"][0]
        tip_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:tip"][0]
        root_chord = inputs["data:geometry:wing:root:chord"][0]
        kink_chord = inputs["data:geometry:wing:kink:chord"][0]
        tip_chord = inputs["data:geometry:wing:tip:chord"][0]

        #  Wing box centers locations --------------------------------------------------------------
        x_box_root = (root_rear_spar_ratio + root_front_spar_ratio) * root_chord * 0.5 + x_root
        x_box_kink = (kink_rear_spar_ratio + kink_front_spar_ratio) * kink_chord * 0.5 + x_kink
        x_box_tip = (tip_rear_spar_ratio + tip_front_spar_ratio) * tip_chord * 0.5 + x_tip

        y_interp = [0.0, y_root, y_kink, y_tip]
        x_interp = [x_box_root, x_box_root, x_box_kink, x_box_tip]
        z_interp = [z_root, z_root, z_kink, z_tip]

        f_x = interp(y_interp, x_interp)
        f_z = interp(y_interp, z_interp)

        #  Number of section (cuts) for each wing geometric section (belly, kink, tip) -------------
        belly_ratio = y_root / y_tip
        kink_ratio = (y_kink - y_root) / y_tip
        if y_root != 0 and int(np.round(belly_ratio * n_secs)) < 1:
            n_secs_belly = 1
        else:
            n_secs_belly = int(np.round(belly_ratio * n_secs))
        if y_kink != y_root and int(np.round(kink_ratio * n_secs)) < 1:
            n_secs_kink = 1
        else:
            n_secs_kink = int(np.round(kink_ratio * n_secs))
        n_secs_tip = n_secs - n_secs_kink - n_secs_belly

        #  Belly to root sections spanwise location
        y_secs_belly = np.linspace(0, y_root, n_secs_belly, endpoint=False)
        #  Root to kink sections spanwise location
        y_secs_kink = np.linspace(y_root, y_kink, n_secs_kink, endpoint=False)
        #  Kink to tip sections spanwise location
        y_secs_tip = np.linspace(y_kink, y_tip, n_secs_tip + 1)

        #  Gathering sections locations
        y_box = np.hstack((y_secs_belly, y_secs_kink, y_secs_tip)).reshape((n_secs + 1, 1))

        #  Nodes coordinates interpolation ---------------------------------------------------------
        x_box = f_x(y_box)
        z_box = f_z(y_box)
        xyz_r = np.hstack((x_box, y_box, z_box))
        xyz_l = np.hstack((x_box, -y_box, z_box))

        outputs["data:aerostructural:structure:wing:nodes"] = np.vstack((xyz_r, xyz_l))
