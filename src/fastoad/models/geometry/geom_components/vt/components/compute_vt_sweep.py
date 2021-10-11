"""
    Estimation of vertical tail sweeps
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


# TODO: HT and VT components are similar --> factorize
class ComputeVTSweep(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Vertical tail sweeps estimation"""

    def setup(self):
        self.add_input("data:geometry:vertical_tail:span", val=np.nan, units="m")
        self.add_input("data:geometry:vertical_tail:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:vertical_tail:tip:chord", val=np.nan, units="m")
        self.add_input("data:geometry:vertical_tail:sweep_25", val=np.nan, units="deg")

        self.add_output("data:geometry:vertical_tail:sweep_0", units="deg")
        self.add_output("data:geometry:vertical_tail:sweep_100", units="deg")

    def setup_partials(self):
        self.declare_partials("data:geometry:vertical_tail:sweep_0", "*", method="fd")
        self.declare_partials("data:geometry:vertical_tail:sweep_100", "*", method="fd")

    def compute(self, inputs, outputs):
        root_chord = inputs["data:geometry:vertical_tail:root:chord"]
        tip_chord = inputs["data:geometry:vertical_tail:tip:chord"]
        sweep_25_vt = inputs["data:geometry:vertical_tail:sweep_25"]
        b_v = inputs["data:geometry:vertical_tail:span"]

        sweep_0_vt = (
            (
                math.pi / 2
                - math.atan(
                    b_v
                    / (
                        0.25 * root_chord
                        - 0.25 * tip_chord
                        + b_v * math.tan(sweep_25_vt / 180.0 * math.pi)
                    )
                )
            )
            / math.pi
            * 180.0
        )
        sweep_100_vt = (
            (
                math.pi / 2
                - math.atan(
                    b_v
                    / (
                        b_v * math.tan(sweep_25_vt / 180.0 * math.pi)
                        - 0.75 * root_chord
                        + 0.75 * tip_chord
                    )
                )
            )
            / math.pi
            * 180.0
        )

        outputs["data:geometry:vertical_tail:sweep_0"] = sweep_0_vt
        outputs["data:geometry:vertical_tail:sweep_100"] = sweep_100_vt
