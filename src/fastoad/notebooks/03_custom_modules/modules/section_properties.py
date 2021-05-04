"""
This module aims to compute section properties of a beam given width and height
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("fastoad.beam_problem.geometry")
class RectangularSection(om.ExplicitComponent):
    def setup(self):

        self.add_input("data:beam_problem:geometry:l", val=np.nan, desc="Section width", units="m")
        self.add_input(
            "data:beam_problem:geometry:Ixx",
            val=np.nan,
            desc="Section second moment of area along w.r.t. x axis",
            units="m**4",
        )
        self.add_output("data:beam_problem:geometry:h", val=0.01, desc="Section height", units="m")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        l = inputs["data:beam_problem:geometry:l"]
        I_xx = inputs["data:beam_problem:geometry:Ixx"]

        outputs["data:beam_problem:geometry:h"] = (12 * I_xx / l) ** (1 / 3)
