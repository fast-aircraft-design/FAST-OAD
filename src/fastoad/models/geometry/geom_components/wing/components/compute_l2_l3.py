"""
    Estimation of wing chords (l2 and l3)
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


class ComputeL2AndL3Wing(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Wing chords (l2 and l3) estimation"""

    def setup(self):
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")
        self.add_input("data:geometry:wing:sweep_25", val=np.nan, units="deg")
        self.add_input("data:geometry:wing:root:virtual_chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:root:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:kink:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:virtual_taper_ratio", val=np.nan)
        self.add_input("data:geometry:fuselage:maximum_width", val=np.nan, units="m")

        self.add_output("data:geometry:wing:root:chord", units="m")
        self.add_output("data:geometry:wing:kink:chord", units="m")
        self.add_output("data:geometry:wing:taper_ratio")

    def setup_partials(self):
        self.declare_partials(
            "data:geometry:wing:root:chord",
            [
                "data:geometry:wing:root:virtual_chord",
                "data:geometry:wing:root:y",
                "data:geometry:wing:kink:y",
                "data:geometry:wing:virtual_taper_ratio",
                "data:geometry:wing:span",
                "data:geometry:fuselage:maximum_width",
                "data:geometry:wing:sweep_25",
            ],
            method="fd",
        )
        self.declare_partials(
            "data:geometry:wing:kink:chord",
            [
                "data:geometry:wing:root:virtual_chord",
                "data:geometry:wing:tip:chord",
                "data:geometry:wing:root:y",
                "data:geometry:wing:kink:y",
                "data:geometry:wing:tip:y",
            ],
            method="fd",
        )

    def compute(self, inputs, outputs):
        l1_wing = inputs["data:geometry:wing:root:virtual_chord"]
        l4_wing = inputs["data:geometry:wing:tip:chord"]
        y2_wing = inputs["data:geometry:wing:root:y"]
        y3_wing = inputs["data:geometry:wing:kink:y"]
        y4_wing = inputs["data:geometry:wing:tip:y"]
        span = inputs["data:geometry:wing:span"]
        width_max = inputs["data:geometry:fuselage:maximum_width"]
        virtual_taper_ratio = inputs["data:geometry:wing:virtual_taper_ratio"]
        sweep_25 = inputs["data:geometry:wing:sweep_25"]

        l2_wing = l1_wing + (y3_wing - y2_wing) * (
            math.tan(sweep_25 / 180.0 * math.pi)
            - 3.0 / 2.0 * (1.0 - virtual_taper_ratio) / (span - width_max) * l1_wing
        )

        l3_wing = l4_wing + (l1_wing - l4_wing) * (y4_wing - y3_wing) / (y4_wing - y2_wing)

        outputs["data:geometry:wing:root:chord"] = l2_wing
        outputs["data:geometry:wing:kink:chord"] = l3_wing
        outputs["data:geometry:wing:taper_ratio"] = l4_wing / l2_wing
