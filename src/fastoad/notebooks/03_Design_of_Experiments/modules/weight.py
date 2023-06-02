"""
Computation of beam linear weight.
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


@oad.RegisterOpenMDAOSystem("tutorial.beam_problem.weight")
class LinearWeight(om.ExplicitComponent):
    """
    Computes beam linear weight given its dimensions.
    """

    def setup(self):

        self.add_input("data:geometry:l", val=np.nan, units="m")
        self.add_input("data:geometry:h", val=np.nan, units="m")
        self.add_input("data:material:density", val=np.nan, units="kg/m**3")

        self.add_output("data:weight:linear_weight", val=10.0, units="N/m")

    def setup_partials(self):

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):

        l = inputs["data:geometry:l"]
        h = inputs["data:geometry:h"]
        rho = inputs["data:material:density"]

        outputs["data:weight:linear_weight"] = l * h * rho * 9.81
