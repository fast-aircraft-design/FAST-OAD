"""
Computation of wing position
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

import numpy as np
import openmdao.api as om


class ComputeWingPosition(om.ImplicitComponent):
    """
    An implicit component to solve the wing position
    """

    def setup(self):
        self.add_input("data:handling_qualities:static_margin", val=np.nan)
        self.add_input("data:handling_qualities:static_margin:target", val=np.nan)
        self.add_input("data:geometry:fuselage:length", val=np.nan, units="m")

        self.add_output("data:geometry:wing:MAC:at25percent:x", val=17.0, units="m")

        self.declare_partials(of="*", wrt="*", method="exact")

    def apply_nonlinear(self, inputs, outputs, residuals):
        static_margin = inputs["data:handling_qualities:static_margin"]
        target_static_margin = inputs["data:handling_qualities:static_margin:target"]

        residuals["data:geometry:wing:MAC:at25percent:x"] = static_margin - target_static_margin

    def guess_nonlinear(self, inputs, outputs, resids):
        # Check residuals
        if np.abs(resids["data:geometry:wing:MAC:at25percent:x"]) > 1.0e-1:
            outputs["data:geometry:wing:MAC:at25percent:x"] = (
                inputs["data:geometry:fuselage:length"] * 0.45
            )

    def linearize(self, inputs, outputs, jacobian):

        jacobian[
            "data:geometry:wing:MAC:at25percent:x", "data:handling_qualities:static_margin"
        ] = 1.0
        jacobian[
            "data:geometry:wing:MAC:at25percent:x", "data:handling_qualities:static_margin:target"
        ] = -1.0
        jacobian[
            "data:geometry:wing:MAC:at25percent:x", "data:geometry:wing:MAC:at25percent:x"
        ] = 0.0
