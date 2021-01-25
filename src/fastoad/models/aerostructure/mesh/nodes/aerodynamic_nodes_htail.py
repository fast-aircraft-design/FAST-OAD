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
from scipy.interpolate import interp1d as interp


class AerodynamicNodesHtail(om.ExplicitComponent):
    """
    Compute horizontal tail aerodynamic mesh nodes coordinates
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]
        # Declare inputs ---------------------------------------------------------------------------
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:MAC:at25percent:x:local", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:MAC:length", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:span", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:sweep_0", val=np.nan, units="rad")
        self.add_input("data:geometry:horizontal_tail:root:z", val=0.0)
        self.add_input("data:geometry:horizontal_tail:tip:z", val=0.0)
        # Declare outputs --------------------------------------------------------------------------

        self.add_output(
            "data:aerostructural:aerodynamic:horizontal_tail:nodes",
            val=np.nan,
            shape=((n_secs + 1) * 2, 3),
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]
        # Prepare inputs ---------------------------------------------------------------------------
        x_root = (
            inputs["data:geometry:wing:MAC:at25percent:x"][0]
            + inputs["data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"][0]
            - 0.25 * inputs["data:geometry:horizontal_tail:MAC:length"][0]
            - inputs["data:geometry:horizontal_tail:MAC:at25percent:x:local"][0]
        )
        x_tip = x_root + inputs["data:geometry:horizontal_tail:span"][0] / 2 * np.tan(
            inputs["data:geometry:horizontal_tail:sweep_0"][0]
        )
        x_root = x_root
        x_tip = x_tip
        y_tip = inputs["data:geometry:horizontal_tail:span"][0] / 2
        z_root = inputs["data:geometry:horizontal_tail:root:z"][0]
        z_tip = inputs["data:geometry:horizontal_tail:tip:z"][0]

        x_interp = [x_root, x_tip]
        y_interp = [0.0, y_tip]
        z_interp = [z_root, z_tip]

        f_x = interp(y_interp, x_interp)
        f_z = interp(y_interp, z_interp)

        #  Nodes coordinates interpolation ---------------------------------------------------------
        y_le = np.linspace(0.0, y_tip, n_secs + 1)
        x_le = f_x(y_le)
        z_le = f_z(y_le)

        #  Symmetry anc sides concatenation --------------------------------------------------------
        xyz_r = np.hstack((x_le[:, np.newaxis], y_le[:, np.newaxis], z_le[:, np.newaxis]))
        xyz_l = np.hstack((x_le[:, np.newaxis], -y_le[:, np.newaxis], z_le[:, np.newaxis]))

        outputs["data:aerostructural:aerodynamic:horizontal_tail:nodes"] = np.vstack((xyz_r, xyz_l))

    # @staticmethod
    # def _get_nodes_loc(n_sections, dimensions):
    #     y_le = np.linspace(0.0, dimensions["y_tip"][0], n_sections + 1)
    #
    #     x_le = np.zeros((n_sections + 1, 1))
    #     z_le = np.zeros((n_sections + 1, 1))
    #     for i in range(0, np.size(y_le)):
    #         x_le[i] = (
    #             y_le[i]
    #             * (dimensions["x_tip"][0] - dimensions["x_root"][0])
    #             / dimensions["y_tip"][0]
    #             + dimensions["x_root"]
    #         )  # y_root assumed = 0.
    #         z_le[i] = (
    #             y_le[i]
    #             * (dimensions["z_tip"][0] - dimensions["z_root"][0])
    #             / dimensions["y_tip"][0]
    #             + dimensions["z_root"]
    #         )  # y_root assumed = 0.
    #     xyz_r = np.hstack((x_le, y_le[:, np.newaxis], z_le))  # right tail coordinates
    #     xyz_l = np.hstack((x_le, -y_le[:, np.newaxis], z_le))  # symmetry for left tail coordinates
    #     return np.vstack((xyz_r, xyz_l))
