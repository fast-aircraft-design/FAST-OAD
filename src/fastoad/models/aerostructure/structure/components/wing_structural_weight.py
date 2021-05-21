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


class WingStructuralWeight(om.ExplicitComponent):
    def setup(self):
        self.add_input("data:aerostructural:structure:wing:nodes", val=np.nan, shape_by_conn=True)
        self.add_input(
            "data:aerostructural:structure:wing:beam_properties", val=np.nan, shape_by_conn=True
        )
        self.add_input("data:aerostructural:structure:wing:material:density", val=2810.0)

        self.add_output("data:weight:structural_weight:wing", val=np.nan)

        self.declare_partials("*", "*", method="fd")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        nodes = inputs["data:aerostructural:structure:wing:nodes"]
        area = inputs["data:aerostructural:structure:wing:beam_properties"][:, 0]
        rho = inputs["data:aerostructural:structure:wing:material:density"]

        weight = 0
        for idx, a in enumerate(area):
            weight += a * rho * np.linalg.norm(nodes[idx + 1, :] - nodes[idx, :])

        outputs["data:weight:structural_weight:wing"] = weight
