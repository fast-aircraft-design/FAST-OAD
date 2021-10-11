"""
    Estimation of wing sweeps
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


class ComputeSweepWing(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Wing sweeps estimation"""

    def setup(self):
        self.add_input("data:geometry:wing:kink:leading_edge:x:local", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:leading_edge:x:local", val=np.nan, units="m")
        self.add_input("data:geometry:wing:root:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:kink:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:kink:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:chord", val=np.nan, units="m")

        self.add_output("data:geometry:wing:sweep_0", units="deg")
        self.add_output("data:geometry:wing:sweep_100_inner", units="deg")
        self.add_output("data:geometry:wing:sweep_100_outer", units="deg")

    def setup_partials(self):
        self.declare_partials(
            "data:geometry:wing:sweep_0",
            [
                "data:geometry:wing:kink:leading_edge:x:local",
                "data:geometry:wing:root:y",
                "data:geometry:wing:kink:y",
            ],
            method="fd",
        )
        self.declare_partials(
            "data:geometry:wing:sweep_100_inner",
            [
                "data:geometry:wing:kink:leading_edge:x:local",
                "data:geometry:wing:root:chord",
                "data:geometry:wing:root:y",
                "data:geometry:wing:kink:y",
                "data:geometry:wing:kink:chord",
            ],
            method="fd",
        )
        self.declare_partials(
            "data:geometry:wing:sweep_100_outer",
            [
                "data:geometry:wing:kink:leading_edge:x:local",
                "data:geometry:wing:tip:leading_edge:x:local",
                "data:geometry:wing:kink:y",
                "data:geometry:wing:tip:y",
                "data:geometry:wing:kink:chord",
                "data:geometry:wing:tip:chord",
            ],
            method="fd",
        )

    def compute(self, inputs, outputs):
        x3_wing = inputs["data:geometry:wing:kink:leading_edge:x:local"]
        x4_wing = inputs["data:geometry:wing:tip:leading_edge:x:local"]
        y2_wing = inputs["data:geometry:wing:root:y"]
        y3_wing = inputs["data:geometry:wing:kink:y"]
        y4_wing = inputs["data:geometry:wing:tip:y"]
        l2_wing = inputs["data:geometry:wing:root:chord"]
        l3_wing = inputs["data:geometry:wing:kink:chord"]
        l4_wing = inputs["data:geometry:wing:tip:chord"]

        outputs["data:geometry:wing:sweep_0"] = (
            math.atan(x3_wing / (y3_wing - y2_wing)) / math.pi * 180.0
        )
        outputs["data:geometry:wing:sweep_100_inner"] = (
            math.atan((x3_wing + l3_wing - l2_wing) / (y3_wing - y2_wing)) / math.pi * 180
        )
        outputs["data:geometry:wing:sweep_100_outer"] = (
            math.atan((x4_wing + l4_wing - x3_wing - l3_wing) / (y4_wing - y3_wing))
            / math.pi
            * 180.0
        )
