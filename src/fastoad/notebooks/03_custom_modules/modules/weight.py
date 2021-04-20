"""
This module aims to compute beam linear weight given its dimensions
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


@oad.RegisterOpenMDAOSystem("fastoad.beam_problem.weight")
class LinearWeigth(om.ExplicitComponent):
    def setup(self):

        self.add_input("data:beam_problem:geometry:l", val=np.nan, desc="Section width")
        self.add_input("data:beam_problem:geometry:h", val=np.nan, desc="Section height")
        self.add_input("data:beam_problem:material:density", val=np.nan, desc="material density")

        self.add_output(
            "data:beam_problem:weigth:linear_weight", val=10.0, desc="beam linear weight"
        )

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):

        l = inputs["data:beam_problem:geometry:l"]
        h = inputs["data:beam_problem:geometry:h"]
        rho = inputs["data:beam_problem:material:density"]

        outputs["data:beam_problem:weigth:linear_weight"] = l * h * rho
