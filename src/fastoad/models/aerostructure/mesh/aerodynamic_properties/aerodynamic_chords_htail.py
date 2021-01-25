"""
Computes Aerodynamic htail  mesh sections length
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


class AerodynamicChordsHtail(om.ExplicitComponent):
    """
    Computes horizontal tail aerodynamic mesh sections length
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]
        self.add_input("data:geometry:horizontal_tail:span", val=np.nan, units="m")

        self.add_input("data:geometry:horizontal_tail:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:tip:chord", val=np.nan, units="m")

        self.add_input("data:aerostructural:aerodynamic:horizontal_tail:nodes", shape_by_conn=True)

        self.add_output(
            "data:aerostructural:aerodynamic:horizontal_tail:chords",
            val=np.nan,
            shape=((n_secs + 1) * 2),
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]

        #  Characteristic points -------------------------------------------------------------------
        y_tip = inputs["data:geometry:horizontal_tail:span"][0] / 2
        root_chord = inputs["data:geometry:horizontal_tail:root:chord"][0]
        tip_chord = inputs["data:geometry:horizontal_tail:tip:chord"][0]

        y_interp = [0.0, y_tip]
        chord_interp = [root_chord, tip_chord]
        f_c = interp(y_interp, chord_interp)

        #  Chords interpolation --------------------------------------------------------------------
        y_le = inputs["data:aerostructural:aerodynamic:horizontal_tail:nodes"][:, 1]
        chords = f_c(np.abs(y_le))

        outputs["data:aerostructural:aerodynamic:horizontal_tail:chords"] = chords

    # @staticmethod
    # def _get_chord_len(n_sections, dimensions, y_le):
    #     chords = np.zeros((n_sections + 1) * 2)
    #     for i in range(0, np.size(y_le)):
    #         chords[i] = (
    #             np.abs(y_le[i])
    #             * (dimensions["tip_chord"][0] - dimensions["root_chord"][0])
    #             / dimensions["y_tip"][0]
    #             + dimensions["root_chord"][0]
    #         )
    #     return chords
