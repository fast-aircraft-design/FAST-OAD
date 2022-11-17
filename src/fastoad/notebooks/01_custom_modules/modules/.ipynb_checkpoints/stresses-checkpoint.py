"""
Computation of beam section that leads to yield stress.
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("tutorial.beam_problem.stresses")
class Stress(om.ExplicitComponent):
    """
    Computes needed beam section second moment of area that leads to yield stress, given force and
    material properties.
    """

    def setup(self):

        self.add_input("data:geometry:L", val=np.nan, units="m")
        self.add_input("data:geometry:h", val=np.nan, units="m")
        self.add_input("data:forces:F", val=np.nan, units="N")
        self.add_input("data:weight:linear_weight", val=np.nan, units="N/m")
        self.add_input("data:material:yield_stress", val=np.nan, units="Pa")

        self.add_output("data:geometry:Ixx", val=1e-5, units="m**4")

    def setup_partials(self):

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):

        L = inputs["data:geometry:L"]
        h = inputs["data:geometry:h"]
        F = inputs["data:forces:F"]
        w = inputs["data:weight:linear_weight"]
        s = inputs["data:material:yield_stress"]

        # Max bending location along the beam
        if w * L - F > 0:
            y_max = (w * L - F) / w
        else:
            y_max = 0
        outputs["data:geometry:Ixx"] = (L - y_max) * (F - 0.5 * w * (L - y_max)) * h / (2 * s)
