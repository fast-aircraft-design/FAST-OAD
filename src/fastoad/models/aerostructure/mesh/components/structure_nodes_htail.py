"""
This module computes structure nodes coordinates for Horizontal tail plane
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


class StructureNodesHtail(om.ExplicitComponent):
    """
    This Class compute HTP structure nodes coordinates based on "number_of_sections" options value
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]

        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:sweep_0", val=np.nan, units="rad")
        self.add_input("data:geometry:horizontal_tail:span", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:root:chord", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:tip:chord", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:MAC:at25percent:x:local", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:root:z", val=np.zeros(1))
        self.add_input("data:geometry:horizontal_tail:tip:z", val=np.zeros(1))
        # self.add_input("settings:aerostructural:horizontal_tail:struct_sections", val=np.nan)
        self.add_output(
            "data:aerostructural:structure:horizontal_tail:nodes",
            val=np.nan,
            shape=((n_secs + 1) * 2, 3),
        )

    def compute(self, inputs, outputs):

        n_secs = self.options["number_of_sections"]

        #  Characteristic points and lengths -------------------------------------------------------
        x_root = (
            inputs["data:geometry:wing:MAC:at25percent:x"][0]
            + inputs["data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"][0]
            - inputs["data:geometry:horizontal_tail:MAC:at25percent:x:local"][0]
        )
        x_tip = x_root + inputs["data:geometry:horizontal_tail:span"][0] * 0.5 * np.tan(
            inputs["data:geometry:horizontal_tail:sweep_0"][0]
        )
        y_root = 0.0
        y_tip = inputs["data:geometry:horizontal_tail:span"][0] * 0.5
        z_root = inputs["data:geometry:horizontal_tail:root:z"][0]
        z_tip = inputs["data:geometry:horizontal_tail:tip:z"][0]
        root_chord = inputs["data:geometry:horizontal_tail:root:chord"][0]
        tip_chord = inputs["data:geometry:horizontal_tail:tip:chord"][0]

        #  HTP Box centers locations ---------------------------------------------------------------

        x_box_root = x_root + 0.5 * root_chord  # Box is assumed centered along mid-chord axis
        x_box_tip = x_tip + 0.5 * tip_chord

        x_interp = [x_box_root, x_box_tip]
        y_interp = [y_root, y_tip]
        z_interp = [z_root, z_tip]

        f_x = interp(y_interp, x_interp)
        f_z = interp(y_interp, z_interp)

        #  Nodes coordinates interpolations --------------------------------------------------------
        y_box = np.linspace(y_root, y_tip, n_secs + 1).reshape((n_secs + 1, 1))
        x_box = f_x(y_box)
        z_box = f_z(y_box)

        xyz_r = np.hstack((x_box, y_box, z_box))
        xyz_l = np.hstack((x_box, -y_box, z_box))

        outputs["data:aerostructural:structure:horizontal_tail:nodes"] = np.vstack((xyz_r, xyz_l))
