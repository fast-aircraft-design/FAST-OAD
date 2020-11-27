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


class AerodynamicNodesHtail(om.ExplicitComponent):
    """
    Compute horizontal tail aerodynamic mesh nodes coordinates
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]
        # Declare inputs ---------------------------------------------------------------------------
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:MAC:at25percent:x:local", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:span", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:sweep_0", val=np.nan, units="rad")
        self.add_input("data:geometry:horizontal_tail:root:z", val=0.0, units="m")
        self.add_input("data:geometry:horizontal_tail:tip:z", val=0.0, units="m")
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
            inputs["data:geometry:wing:MAC:at25percent:x"]
            + inputs["data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"]
            - 0.25 * inputs["data:geometry:horizontal_tail:MAC:length"]
            - inputs["data:geometry:horizontal_tail:MAC:at25percent:x:local"]
        )
        x_tip = x_root + inputs["data:geometry:horizontal_tail:span"] / 2 * np.tan(
            inputs["data:geometry:horizontal_tail:sweep_0"]
        )
        dim = {
            "x_root": x_root,
            "x_tip": x_tip,
            "y_tip": inputs["data:geometry:horizontal_tail:span"] / 2,
            "z_root": inputs["data:geometry:horizontal_tail:root:z"],
            "z_tip": inputs["data:geometry:horizontal_tail:tip:z"],
        }

        outputs["data:aerostructural:aerodynamic:horizontal_tail:nodes"] = self._get_nodes_loc(
            n_secs, dim
        )

    @staticmethod
    def _get_nodes_loc(n_sections, dimensions):
        y_le = np.linspace(0.0, dimensions["y_tip"], n_sections + 1)

        x_le = np.zeros((n_sections + 1, 1))
        z_le = np.zeros((n_sections + 1, 1))
        for i in range(0, np.size(y_le)):
            x_le[i] = (
                y_le[i] * (dimensions["x_tip"] - dimensions["x_root"]) / dimensions["y_tip"]
                + dimensions["x_root"]
            )  # y_root assumed = 0.
            z_le[i] = (
                y_le[i] * (dimensions["z_tip"] - dimensions["z_root"]) / dimensions["y_tip"]
                + dimensions["z_root"]
            )  # y_root assumed = 0.
        xyz_r = np.hstack((x_le, y_le[:, np.newaxis], z_le))  # right tail coordinates
        xyz_l = np.hstack((x_le, -y_le[:, np.newaxis], z_le))  # symmetry for left tail coordinates
        return np.vstack((xyz_r, xyz_l))
