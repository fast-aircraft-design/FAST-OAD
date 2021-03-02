"""
Computes Aerodynamic wing mesh nodes locations
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


class AerodynamicNodesWing(om.ExplicitComponent):
    """
    Computes wing aerodynamic mesh nodes coordinates
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]
        # Declare inputs ---------------------------------------------------------------------------
        self.add_input("data:geometry:wing:MAC:length", val=np.nan)
        self.add_input("data:geometry:wing:MAC:leading_edge:x:local", val=np.nan)
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:geometry:wing:root:y", val=np.nan)
        self.add_input("data:geometry:wing:root:z", val=0.0)
        self.add_input("data:geometry:wing:kink:leading_edge:x:local", val=np.nan)
        self.add_input("data:geometry:wing:kink:y", val=np.nan)
        self.add_input("data:geometry:wing:kink:z", val=0.0)
        self.add_input("data:geometry:wing:tip:leading_edge:x:local", val=np.nan)
        self.add_input("data:geometry:wing:tip:y", val=np.nan)
        self.add_input("data:geometry:wing:tip:z", val=0.0)

        self.add_output(
            "data:aerostructural:aerodynamic:wing:nodes", val=np.nan, shape=((n_secs + 1) * 2, 3)
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]

        #  Characteristic points
        x_root = (
            inputs["data:geometry:wing:MAC:at25percent:x"][0]
            - 0.25 * inputs["data:geometry:wing:MAC:length"][0]
            - inputs["data:geometry:wing:MAC:leading_edge:x:local"][0]
        )
        x_kink = x_root + inputs["data:geometry:wing:kink:leading_edge:x:local"][0]
        x_tip = x_root + inputs["data:geometry:wing:tip:leading_edge:x:local"][0]
        y_root = inputs["data:geometry:wing:root:y"][0]
        y_kink = inputs["data:geometry:wing:kink:y"][0]
        y_tip = inputs["data:geometry:wing:tip:y"][0]
        z_root = inputs["data:geometry:wing:root:z"][0]
        z_kink = inputs["data:geometry:wing:kink:z"][0]
        z_tip = inputs["data:geometry:wing:tip:z"][0]

        #  Ratio of wing sections
        belly_ratio = y_root / y_tip
        kink_ratio = (y_kink - y_root) / y_tip

        if 0 < int(np.round(belly_ratio * n_secs)) < 1:
            n_sections_belly = 1
        else:
            n_sections_belly = int(np.round(belly_ratio * n_secs))
        if 0 < int(np.round(kink_ratio * n_secs)) < 1:
            n_sections_kink = 1
        else:
            n_sections_kink = int(np.round(kink_ratio * n_secs))
        n_sections_tip = n_secs - n_sections_kink - n_sections_belly

        y_interp = [0.0, y_root, y_kink, y_tip]
        x_interp = [x_root, x_root, x_kink, x_tip]
        z_interp = [z_root, z_root, z_kink, z_tip]

        f_x = interp(y_interp, x_interp, "linear")
        f_z = interp(y_interp, z_interp, "linear")

        #  Belly to root sections spanwise location
        y_sections_belly = np.linspace(0, y_root, n_sections_belly, endpoint=False)
        #  Root to kink sections spanwise location
        y_section_kink = np.linspace(y_root, y_kink, n_sections_kink, endpoint=False)
        #  Kink to tip sections spanwise location
        y_section_tip = np.linspace(y_kink, y_tip, n_sections_tip + 1)

        #  Nodes coordinates interpolation
        y_le = np.hstack((y_sections_belly, y_section_kink, y_section_tip))
        x_le = f_x(y_le)
        z_le = f_z(y_le)
        # right wing coordinates
        xyz_r = np.hstack((x_le[:, np.newaxis], y_le[:, np.newaxis], z_le[:, np.newaxis]))
        xyz_l = np.hstack((x_le[:, np.newaxis], -y_le[:, np.newaxis], z_le[:, np.newaxis]))

        outputs["data:aerostructural:aerodynamic:wing:nodes"] = np.vstack((xyz_r, xyz_l))

    # @staticmethod
    # def _get_nodes_loc(n_sections, dimensions):
    #     wing_span = dimensions["y_tip"]
    #     root_ratio = dimensions["y_root"] / wing_span
    #     kink_ratio = (dimensions["y_kink"] - dimensions["y_root"]) / wing_span
    #     if int(np.round(root_ratio * n_sections)[0]) < 1:
    #         n_sections_root = 1
    #     else:
    #         n_sections_root = int(np.round(root_ratio * n_sections)[0])
    #     if int(np.round(kink_ratio * n_sections)[0]) < 1:
    #         n_sections_kink = 1
    #     else:
    #         n_sections_kink = int(np.round(kink_ratio * n_sections)[0])
    #     n_sections_tip = n_sections - n_sections_kink - n_sections_root
    #
    #     y_le = np.hstack(
    #         (
    #             np.linspace(
    #                 dimensions["y_root"][0],
    #                 dimensions["y_kink"][0],
    #                 n_sections_kink,
    #                 endpoint=False,
    #             ),
    #             np.linspace(
    #                 dimensions["y_root"][0],
    #                 dimensions["y_kink"][0],
    #                 n_sections_kink,
    #                 endpoint=False,
    #             ),
    #             np.linspace(
    #                 dimensions["y_kink"][0],
    #                 dimensions["y_tip"][0],
    #                 n_sections_tip + 1),
    #         )
    #     )
    #     x_le = np.zeros((n_sections + 2, 1))
    #     z_le = np.zeros((n_sections + 2, 1))
    #     x_le[0] = dimensions["x_root"][0]
    #     z_le[0] = dimensions["z_root"][0]
    #     for i in range(1, np.size(y_le)):
    #         if y_le[i] <= dimensions["y_kink"][0]:
    #             x_le[i] = (y_le[i] - dimensions["y_root"]) * (
    #                 dimensions["x_kink"][0] - dimensions["x_root"][0]
    #             ) / (dimensions["y_kink"][0] - dimensions["y_root"][0]) + dimensions["x_root"][0]
    #             z_le[i] = (y_le[i] - dimensions["y_root"][0]) * (
    #                 dimensions["z_kink"][0] - dimensions["z_root"][0]
    #             ) / (dimensions["y_kink"][0] - dimensions["y_root"][0]) + dimensions["z_root"][0]
    #         else:
    #             x_le[i] = (y_le[i] - dimensions["y_kink"][0]) * (
    #                 dimensions["x_tip"][0] - dimensions["x_kink"][0]
    #             ) / (dimensions["y_tip"][0] - dimensions["y_kink"][0]) + dimensions["x_kink"][0]
    #             z_le[i] = (y_le[i] - dimensions["y_kink"][0]) * (
    #                 dimensions["z_tip"][0] - dimensions["z_kink"][0]
    #             ) / (dimensions["y_tip"][0] - dimensions["y_kink"][0]) + dimensions["z_kink"][0]
    #
    #     xyz_r = np.hstack((x_le, y_le[:, np.newaxis], z_le))  # right wing coordinates
    #     xyz_l = np.hstack((x_le, -y_le[:, np.newaxis], z_le))  # symmetry for left wing coordinates
    #     return np.vstack((xyz_r, xyz_l))
