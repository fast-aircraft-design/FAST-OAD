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


class AerodynamicNodesWing(om.ExplicitComponent):
    """
    Computes wing aerodynamic mesh nodes coordinates
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]
        # Declare inputs ---------------------------------------------------------------------------
        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:leading_edge:x:local", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:geometry:wing:root:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:root:z", val=0.0, units="m")
        self.add_input("data:geometry:wing:kink:leading_edge:x:local", val=np.nan, units="m")
        self.add_input("data:geometry:wing:kink:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:kink:z", val=0.0, units="m")
        self.add_input("data:geometry:wing:tip:leading_edge:x:local", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:z", val=0.0, units="m")

        self.add_output(
            "data:aerostructural:aerodynamic:wing:nodes", val=np.nan, shape=((n_secs + 1) * 2, 3)
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]
        x_root = (
            inputs["data:geometry:wing:MAC:at25percent:x"]
            - 0.25 * inputs["data:geometry:wing:MAC:length"]
            - inputs["data:geometry:wing:MAC:leading_edge:x:local"]
        )
        x_kink = x_root + inputs["data:geometry:wing:kink:leading_edge:x:local"]
        x_tip = x_root + inputs["data:geometry:wing:tip:leading_edge:x:local"]
        dim = {
            "x_root": x_root,
            "x_kink": x_kink,
            "x_tip": x_tip,
            "y_root": inputs["data:geometry:wing:root:y"],
            "y_kink": inputs["data:geometry:wing:kink:y"],
            "y_tip": inputs["data:geometry:wing:tip:y"],
            "z_root": inputs["data:geometry:wing:root:z"],
            "z_kink": inputs["data:geometry:wing:kink:z"],
            "z_tip": inputs["data:geometry:wing:tip:z"],
        }

        outputs["data:aerostructural:aerodynamic:wing:nodes"] = self._get_nodes_loc(n_secs, dim)

    @staticmethod
    def _get_nodes_loc(n_sections, dimensions):
        elem_span = dimensions["y_tip"] - dimensions["y_root"]
        kink_ratio = (dimensions["y_kink"] - dimensions["y_root"]) / elem_span
        n_sections_kink = int(np.round(kink_ratio * n_sections)[0])
        n_sections_tip = n_sections - n_sections_kink

        y_le = np.hstack(
            (
                np.linspace(
                    dimensions["y_root"][0],
                    dimensions["y_kink"][0],
                    n_sections_kink,
                    endpoint=False,
                ),
                np.linspace(dimensions["y_kink"][0], dimensions["y_tip"][0], n_sections_tip + 1),
            )
        )
        x_le = np.zeros((n_sections + 1, 1))
        z_le = np.zeros((n_sections + 1, 1))
        for i in range(0, np.size(y_le)):
            if y_le[i] <= dimensions["y_kink"][0]:
                x_le[i] = (y_le[i] - dimensions["y_root"]) * (
                    dimensions["x_kink"][0] - dimensions["x_root"][0]
                ) / (dimensions["y_kink"][0] - dimensions["y_root"][0]) + dimensions["x_root"][0]
                z_le[i] = (y_le[i] - dimensions["y_root"][0]) * (
                    dimensions["z_kink"][0] - dimensions["z_root"][0]
                ) / (dimensions["y_kink"][0] - dimensions["y_root"][0]) + dimensions["z_root"][0]
            else:
                x_le[i] = (y_le[i] - dimensions["y_kink"][0]) * (
                    dimensions["x_tip"][0] - dimensions["x_kink"][0]
                ) / (dimensions["y_tip"][0] - dimensions["y_kink"][0]) + dimensions["x_kink"][0]
                z_le[i] = (y_le[i] - dimensions["y_kink"][0]) * (
                    dimensions["z_tip"][0] - dimensions["z_kink"][0]
                ) / (dimensions["y_tip"][0] - dimensions["y_kink"][0]) + dimensions["z_kink"][0]

        xyz_r = np.hstack((x_le, y_le[:, np.newaxis], z_le))  # right tail coordinates
        xyz_l = np.hstack((x_le, -y_le[:, np.newaxis], z_le))  # symmetry for left tail coordinates
        return np.vstack((xyz_r, xyz_l))
