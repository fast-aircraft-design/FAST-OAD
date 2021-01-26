"""
Compute wing twist for each section
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

import openmdao.api as om
import numpy as np
from scipy.interpolate import interp1d as interp


class AerodynamicTwistWing(om.ExplicitComponent):
    """
    Class to interpolate wing twist for each spanwise section of the wing
    """

    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_sects = self.options["number_of_sections"]
        self.add_input("data:geometry:wing:root:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:kink:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:tip:y", val=np.nan, units="m")

        self.add_input("data:geometry:wing:root:twist", val=np.nan, units="deg")
        self.add_input("data:geometry:wing:kink:twist", val=np.nan, units="deg")
        self.add_input("data:geometry:wing:tip:twist", val=np.nan, units="deg")

        self.add_input("data:aerostructural:aerodynamic:wing:nodes", shape_by_conn=True)

        self.add_output(
            "data:aerostructural:aerodynamic:wing:twist", val=0.0, shape=((n_sects + 1) * 2)
        )

    def compute(self, inputs, outputs):
        n_sects = self.options["number_of_sections"]
        y = [
            0.0,
            inputs["data:geometry:wing:root:y"][0],
            inputs["data:geometry:wing:kink:y"][0],
            inputs["data:geometry:wing:tip:y"][0],
        ]
        twist = [
            inputs["data:geometry:wing:root:twist"][0],
            inputs["data:geometry:wing:root:twist"][0],
            inputs["data:geometry:wing:kink:twist"][0],
            inputs["data:geometry:wing:tip:twist"][0],
        ]
        nodes = inputs["data:aerostructural:aerodynamic:wing:nodes"]
        y_i = nodes[: n_sects + 1, 1]
        f = interp(y, twist, "linear")
        t_ci = f(y_i)
        outputs["data:aerostructural:aerodynamic:wing:twist"] = np.tile(t_ci, 2)
