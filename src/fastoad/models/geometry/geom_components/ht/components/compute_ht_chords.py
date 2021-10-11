"""
    Estimation of horizontal tail chords and span
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


# TODO: is an OpenMDAO component required for this simple calculation ?
class ComputeHTChord(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Horizontal tail chords and span estimation"""

    def setup(self):
        self.add_input("data:geometry:horizontal_tail:aspect_ratio", val=np.nan)
        self.add_input("data:geometry:horizontal_tail:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:horizontal_tail:taper_ratio", val=np.nan)

        self.add_output("data:geometry:horizontal_tail:span", units="m")
        self.add_output("data:geometry:horizontal_tail:root:chord", units="m")
        self.add_output("data:geometry:horizontal_tail:tip:chord", units="m")

    def setup_partials(self):
        self.declare_partials(
            "data:geometry:horizontal_tail:span",
            ["data:geometry:horizontal_tail:area", "data:geometry:horizontal_tail:aspect_ratio"],
            method="fd",
        )
        self.declare_partials("data:geometry:horizontal_tail:root:chord", "*", method="fd")
        self.declare_partials("data:geometry:horizontal_tail:tip:chord", "*", method="fd")

    def compute(self, inputs, outputs):
        lambda_ht = inputs["data:geometry:horizontal_tail:aspect_ratio"]
        s_h = inputs["data:geometry:horizontal_tail:area"]
        taper_ht = inputs["data:geometry:horizontal_tail:taper_ratio"]

        b_h = np.sqrt(max(lambda_ht * s_h, 0.1))
        root_chord = s_h * 2 / (1 + taper_ht) / b_h
        tip_chord = root_chord * taper_ht

        outputs["data:geometry:horizontal_tail:span"] = b_h
        outputs["data:geometry:horizontal_tail:root:chord"] = root_chord
        outputs["data:geometry:horizontal_tail:tip:chord"] = tip_chord
