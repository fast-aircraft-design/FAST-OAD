"""
    Estimation of horizontal tail sweeps
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


class ComputeHTSweep(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Horizontal tail sweeps estimation"""

    def setup(self):
        self.add_input("data:geometry:horizontal_tail:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:tip:chord", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:span", val=np.nan, units="m")
        self.add_input("data:geometry:horizontal_tail:sweep_25", val=np.nan, units="deg")

        self.add_output("data:geometry:horizontal_tail:sweep_0", units="deg")
        self.add_output("data:geometry:horizontal_tail:sweep_100", units="deg")

    def setup_partials(self):
        self.declare_partials("data:geometry:horizontal_tail:sweep_0", "*", method="fd")
        self.declare_partials("data:geometry:horizontal_tail:sweep_100", "*", method="fd")

    def compute(self, inputs, outputs):
        b_h = inputs["data:geometry:horizontal_tail:span"]
        root_chord = inputs["data:geometry:horizontal_tail:root:chord"]
        tip_chord = inputs["data:geometry:horizontal_tail:tip:chord"]
        sweep_25_ht = inputs["data:geometry:horizontal_tail:sweep_25"]

        half_span = b_h / 2.0
        # TODO: The unit conversion can be handled by OpenMDAO
        sweep_0_ht = (
            (
                math.pi / 2
                - math.atan(
                    half_span
                    / (
                        0.25 * root_chord
                        - 0.25 * tip_chord
                        + half_span * math.tan(sweep_25_ht / 180.0 * math.pi)
                    )
                )
            )
            / math.pi
            * 180.0
        )
        sweep_100_ht = (
            (
                math.pi / 2
                - math.atan(
                    half_span
                    / (
                        half_span * math.tan(sweep_25_ht / 180.0 * math.pi)
                        - 0.75 * root_chord
                        + 0.75 * tip_chord
                    )
                )
            )
            / math.pi
            * 180.0
        )

        outputs["data:geometry:horizontal_tail:sweep_0"] = sweep_0_ht
        outputs["data:geometry:horizontal_tail:sweep_100"] = sweep_100_ht
