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


class AerodynamicNodesVtail(om.ExplicitComponent):
    """
    Computes vertical tail aerodynamic mesh nodes coordinates
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:geometry:vertical_tail:MAC:at25percent:x:local", val=np.nan)
        self.add_input("data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan)
        self.add_input("data:geometry:vertical_tail:MAC:length", val=np.nan)
        self.add_input("data:geometry:vertical_tail:span", val=np.nan)
        self.add_input("data:geometry:vertical_tail:sweep_0", val=np.nan, units="rad")
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan)

        self.add_output(
            "data:aerostructural:aerodynamic:vertcal_tail:nodes",
            val=np.nan,
            shape=((n_secs + 1), 3),
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]

        x_root = (
            inputs["data:geometry:wing:MAC:at25percent:x"]
            + inputs["data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25"]
            - 0.25 * inputs["data:geometry:vertical_tail:MAC:length"]
            - inputs["data:geometry:vertical_tail:MAC:at25percent:x:local"]
        )
        x_tip = x_root + inputs["data:geometry:vertical_tail:span"] * np.tan(
            inputs["data:geometry:vertical_tail:sweep_0"]
        )
        z_root = inputs["data:geometry:fuselage:maximum_height"] / 2
        dim = {
            "x_root": x_root,
            "x_tip": x_tip,
            "z_tip": inputs["data:geometry:vertical_tail:span"] + z_root,
            "z_root": z_root,
        }

        outputs["data:aerostructural:aerodynamic:vertical_tail:nodes"] = self._get_nodes_loc(
            n_secs, dim
        )

    @staticmethod
    def _get_nodes_loc(n_sections, dimensions):
        z_le = np.linspace(dimensions["z_root"], dimensions["z_tip"], n_sections + 1)

        x_le = np.zeros((n_sections + 1, 1))
        y_le = np.zeros((n_sections + 1, 1))
        for i in range(0, np.size(y_le)):
            x_le[i] = (z_le[i] - dimensions["z_root"]) * (
                dimensions["x_tip"] - dimensions["x_root"]
            ) / (dimensions["z_tip"] - dimensions["z_root"]) + dimensions["x_root"]
        xyz = np.hstack((x_le, y_le, z_le[:, np.newaxis]))
        return xyz
