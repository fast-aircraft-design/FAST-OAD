"""
    Estimation of horizontal tail mean aerodynamic chords
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
import math

import numpy as np
import openmdao.api as om


# TODO: it would be good to have a function to compute MAC for HT, VT and WING
class ComputeHTMAC(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Horizontal tail mean aerodynamic chord estimation"""

    def setup(self):
        self.add_input("data:geometry:horizontal_tail:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:tip:chord", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:sweep_25", val=np.nan, units="deg")
        self.add_input("data:geometry:horizontal_tail:span", val=np.nan, units="m")

        self.add_output("data:geometry:horizontal_tail:MAC:length", units="m")
        self.add_output("data:geometry:horizontal_tail:MAC:at25percent:x:local", units="m")
        self.add_output("data:geometry:horizontal_tail:MAC:y", units="m")

    def setup_partials(self):
        self.declare_partials(
            "data:geometry:horizontal_tail:MAC:length",
            ["data:geometry:horizontal_tail:root:chord", "data:geometry:horizontal_tail:tip:chord"],
            method="fd",
        )
        self.declare_partials(
            "data:geometry:horizontal_tail:MAC:at25percent:x:local",
            [
                "data:geometry:horizontal_tail:root:chord",
                "data:geometry:horizontal_tail:tip:chord",
                "data:geometry:horizontal_tail:sweep_25",
                "data:geometry:horizontal_tail:span",
            ],
            method="fd",
        )
        self.declare_partials(
            "data:geometry:horizontal_tail:MAC:y",
            [
                "data:geometry:horizontal_tail:root:chord",
                "data:geometry:horizontal_tail:tip:chord",
                "data:geometry:horizontal_tail:span",
            ],
            method="fd",
        )

    def compute(self, inputs, outputs):
        root_chord = inputs["data:geometry:horizontal_tail:root:chord"]
        tip_chord = inputs["data:geometry:horizontal_tail:tip:chord"]
        sweep_25_ht = inputs["data:geometry:horizontal_tail:sweep_25"]
        b_h = inputs["data:geometry:horizontal_tail:span"]

        tmp = (
            root_chord * 0.25 + b_h / 2 * math.tan(sweep_25_ht / 180.0 * math.pi) - tip_chord * 0.25
        )

        mac_ht = (
            (root_chord ** 2 + root_chord * tip_chord + tip_chord ** 2)
            / (tip_chord + root_chord)
            * 2
            / 3
        )
        x0_ht = (tmp * (root_chord + 2 * tip_chord)) / (3 * (root_chord + tip_chord))
        y0_ht = (b_h * (0.5 * root_chord + tip_chord)) / (3 * (root_chord + tip_chord))

        outputs["data:geometry:horizontal_tail:MAC:length"] = mac_ht
        outputs["data:geometry:horizontal_tail:MAC:at25percent:x:local"] = x0_ht
        outputs["data:geometry:horizontal_tail:MAC:y"] = y0_ht
