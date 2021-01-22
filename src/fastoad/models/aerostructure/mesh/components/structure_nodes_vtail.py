"""
This module computes structure nodes coordinates for Vertical tail plane
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


class StructureNodesVtail(om.ExplicitComponent):
    """
    This Class compute VTP structure nodes coordinates based on "number_of_sections" options value
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]

        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan)
        self.add_input("data:geometry:vertical_tail:sweep_0", val=np.nan, units="rad")
        self.add_input("data:geometry:vertical_tail:span", val=np.nan)
        self.add_input("data:geometry:vertical_tail:root:chord", val=np.nan)
        self.add_input("data:geometry:vertical_tail:tip:chord", val=np.nan)
        self.add_input("data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan)
        self.add_input("data:geometry:vertical_tail:MAC:at25percent:x:local", val=np.nan)
        # self.add_input("settings:aerostructural:vertical_tail:struct_sections", val=np.nan)
        self.add_output(
            "data:aerostructural:structure:vertical_tail:nodes", val=np.nan, shape=(n_secs + 1, 3)
        )

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]

        #  Characteristic points and length --------------------------------------------------------
        x_root = (
            inputs["data:geometry:wing:MAC:at25percent:x"][0]
            + inputs["data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25"][0]
            - inputs["data:geometry:vertical_tail:MAC:at25percent:x:local"][0]
        )
        x_tip = x_root + inputs["data:geometry:vertical_tail:span"][0] * np.tan(
            inputs["data:geometry:vertical_tail:sweep_0"][0]
        )
        z_root = 0.5 * inputs["data:geometry:fuselage:maximum_height"][0]
        z_tip = z_root + inputs["data:geometry:vertical_tail:span"][0]
        root_chord = inputs["data:geometry:vertical_tail:root:chord"][0]
        tip_chord = inputs["data:geometry:vertical_tail:tip:chord"][0]

        #  VTP box centers locations ---------------------------------------------------------------
        x_box_root = x_root + 0.5 * root_chord
        x_box_tip = x_tip + 0.5 * tip_chord

        x_interp = [x_box_root, x_box_tip]
        z_interp = [z_root, z_tip]

        f_x = interp(z_interp, x_interp)

        #  Nodes coordinates interpolation ---------------------------------------------------------

        z_box = np.linspace(z_root, z_tip, n_secs + 1).reshape((n_secs + 1, 1))
        x_box = f_x(z_box)
        y_box = np.zeros((n_secs + 1, 1))

        outputs["data:aerostructural:structure:vertical_tail:nodes"] = np.hstack(
            (x_box, y_box, z_box)
        )
