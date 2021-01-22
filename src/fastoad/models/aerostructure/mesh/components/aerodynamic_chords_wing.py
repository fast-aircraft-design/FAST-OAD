"""
Computes Aerodynamic wing mesh sections length
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


class AerodynamicChordsWing(om.ExplicitComponent):
    """
    Computes wing chords length for each section
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]

        self.add_input("data:geometry:wing:root:y", val=np.nan)
        self.add_input("data:geometry:wing:kink:y", val=np.nan)
        self.add_input("data:geometry:wing:tip:y", val=np.nan)

        self.add_input("data:geometry:wing:root:chord", val=np.nan)
        self.add_input("data:geometry:wing:kink:chord", val=np.nan)
        self.add_input("data:geometry:wing:tip:chord", val=np.nan)

        self.add_input("data:aerostructural:aerodynamic:wing:nodes", shape_by_conn=True)

        self.add_output(
            "data:aerostructural:aerodynamic:wing:chords", val=np.nan, shape=((n_secs + 1) * 2),
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]

        #  Characteristic points and lengths -------------------------------------------------------
        y_root = inputs["data:geometry:wing:root:y"][0]
        y_kink = inputs["data:geometry:wing:kink:y"][0]
        y_tip = inputs["data:geometry:wing:tip:y"][0]
        root_chord = inputs["data:geometry:wing:root:chord"][0]
        kink_chord = inputs["data:geometry:wing:kink:chord"][0]
        tip_chord = inputs["data:geometry:wing:tip:chord"][0]

        y_interp = [0.0, y_root, y_kink, y_tip]
        chord_interp = [root_chord, root_chord, kink_chord, tip_chord]
        f_c = interp(y_interp, chord_interp)

        #  Chords interpolation --------------------------------------------------------------------
        y_le = inputs["data:aerostructural:aerodynamic:wing:nodes"][:, 1]
        chords = f_c(np.abs(y_le))

        outputs["data:aerostructural:aerodynamic:wing:chords"] = chords

    # @staticmethod
    # def _get_chord_len(n_sections, dimensions, y_le):
    #     chords = np.zeros((n_sections + 1) * 2)
    #     for idx, y in enumerate(y_le):
    #         if -dimensions["y_kink"] <= y <= dimensions["y_kink"]:
    #             chords[idx] = (np.abs(y) - dimensions["y_root"]) * (
    #                 dimensions["kink_chord"] - dimensions["root_chord"]
    #             ) / (dimensions["y_kink"] - dimensions["y_root"]) + dimensions["root_chord"]
    #         else:
    #             chords[idx] = (np.abs(y) - dimensions["y_kink"]) * (
    #                 dimensions["tip_chord"] - dimensions["kink_chord"]
    #             ) / (dimensions["y_tip"] - dimensions["y_kink"]) + dimensions["kink_chord"]
    #     return chords
