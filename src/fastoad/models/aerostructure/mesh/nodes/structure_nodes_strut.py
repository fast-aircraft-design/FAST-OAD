"""
This module computes structure nodes coordinates for struts
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

import numpy as np
import openmdao.api as om


class StructureNodesStrut(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("number_of_sections", types=int, allow_none=False)
        self.options.declare("has_vertical_strut", types=bool, default=False)

    def setup(self):
        n_secs = self.options["number_of_sections"]

        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:geometry:wing:root:chord", val=np.nan)
        self.add_input("data:geometry:strut:spar_ratio:root", val=np.nan)
        self.add_input(
            "data:geometry:strut:root:leading_edge:x:from_wingMAC25",
            val=np.nan,
            desc="longitudinal location of the strut root leading edge with respect to wing 25% MAC location",
        )
        self.add_input("data:geometry:strut:root:z", val=np.nan)
        self.add_input("data:geometry:wing:tip:chord", val=np.nan)
        self.add_input("data:geometry:strut:spar_ratio:tip", val=np.nan)
        self.add_input(
            "data:geometry:strut:root:leading_edge:x:local",
            val=np.nan,
            desc="longitudinal location of the strut tip leading edge with respect to root",
        )
        self.add_input("data:geometry:strut:tip:y", val=np.nan)
        self.add_input("data:geometry:strut:tip:z", val=np.nan)

        if self.options["has_vertical_strut"]:
            self.add_input("data:geometry:strut:vertical_part_height", val=np.nan)

            self.add_output(
                "data:aerostructural:structure:strut:nodes", val=np.nan, shape=((n_secs + 2) * 2, 3)
            )
        else:
            self.add_output(
                "data:aerostructural:structure:strut:nodes", val=np.nan, shape=((n_secs + 1) * 2, 3)
            )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        x_wing_mac25 = inputs["data:geometry:wing:MAC:at25percent:x"][0]
        root_chord = inputs["data:geometry:wing:root:chord"][0]
        root_spar_ratio = inputs["data:geometry:strut:spar_ratio:root"][0]
        x_root_le_mac25 = inputs["data:geometry:strut:root:leading_edge:x:from_wingMAC25"][0]
        z_root = inputs["data:geometry:strut:root:z"][0]
        tip_chord = inputs["data:geometry:wing:tip:chord"]
        tip_spar_ratio = inputs["data:geometry:strut:spar_ratio:tip"]
        x_tip_local = inputs["data:geometry:strut:root:leading_edge:x:local"]
        y_tip = inputs["data:geometry:strut:tip:y"]
        z_tip = inputs["data:geometry:strut:tip:z"]

        if self.options["has_vertical_strut"]:
            height_vertical_strut = inputs["data:geometry:strut:vertical_part_height"]

        # Root and tip strut spar longitudinal location --------------------------------------------
        x_root_box = x_root_le_mac25 + x_wing_mac25 + root_spar_ratio * root_chord
        x_tip_box = x_root_le_mac25 + x_wing_mac25 + x_tip_local + tip_spar_ratio * tip_chord

        # Strut nodes spanwise coordinates ---------------------------------------------------------
        y = np.linspace(0, y_tip, num=self.options["number_of_sections"] + 1)
        if self.options["has_vertical_strut"]:
            y = np.append(y, y[-1])

        # Strut nodes longitudinal and vertical coordinates interpolation --------------------------

        x = x_root_box + y * (x_tip_box - x_root_box) / y_tip
        z = z_root + y * (z_tip - z_root) / y_tip
        if self.options["has_vertival_strut"]:
            z[-1] = z[-1] + height_vertical_strut

        outputs["data:aerostructural:structure:strut:nodes"] = np.hstack((x, y, z))
