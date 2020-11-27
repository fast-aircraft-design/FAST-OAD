"""
Computes Aerodynamic vtail mesh sections length
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


class AerodynamicChordsVtail(om.ExplicitComponent):
    """
    Computes vertical tail chords length for each aerodynamic section
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]
        self.add_input("data:geometry:vertical_tail:span", val=np.nan, units="m")
        self.add_input("data:geometry:vertical_tail:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:vertical_tail:tip:chord", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan, units="m")

        self.add_input("data:aerostructural:aerodynamic:vertical_tail:nodes", shape_by_conn=True)

        self.add_output(
            "data:aerostructural:aerodynamic:vertical_tail:local_chords",
            val=np.nan,
            shape=(n_secs + 1),
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]
        z_root = inputs["data:geometry:fuselage:maximum_height"] / 2
        dim = {
            "z_root": z_root,
            "z_tip": inputs["data:geometry:vertical_tail:span"] + z_root,
            "root_chord": inputs["data:geometry:vertical_tail:root:chord"],
            "tip_chord": inputs["data:geometry:wing:horizontal_tail:chord"],
        }
        z_le = inputs["data:aerostructural:aerodynamic:vertical_tail:nodes"][:, 2]

        outputs["data:aerostructural:aerodynamic:vertical_tail:local_chords"] = self._get_chord_len(
            n_secs, dim, z_le
        )

    @staticmethod
    def _get_chord_len(n_sections, dimensions, z_le):
        chords = np.zeros((n_sections + 1))
        for i in range(0, np.size(z_le)):
            chords[i] = (z_le[i] - dimensions["z_root"]) * (
                dimensions["tip_chord"] - dimensions["root_chord"]
            ) / (dimensions["z_tip"] - dimensions["z_root"]) + dimensions["root_chord"]
        return chords
