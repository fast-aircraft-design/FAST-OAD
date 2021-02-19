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


class ComponentDisplacements(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("component", types=str)

    def setup(self):
        comp = self.options["component"]
        self.add_input(
            "data:aerostructural:transfer:" + comp + ":matrix", shape_by_conn=True, val=np.nan
        )
        self.add_input(
            "data:aerostructural:structure:" + comp + ":displacements",
            shape_by_conn=True,
            val=np.nan,
        )
        self.add_input(
            "data:aerostructural:aerodynamic:" + comp + ":nodes", val=np.nan, shape_by_conn=True
        )
        self.add_output(
            "data:aerostructural:aerodynamic:" + comp + ":displacements",
            copy_shape="data:aerostructural:aerodynamic:" + comp + ":nodes",
            val=0.0,
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        comp = self.options["component"]
        # Transfer Matrix
        t_mat = inputs["data:aerostructural:transfer:" + comp + ":matrix"]

        # Structural nodes displacements
        disp_s = np.matrix.flatten(
            inputs["data:aerostructural:structure:" + comp + ":displacements"]
        )
        # Aerodynamic nodes displacements
        disp_a = np.dot(t_mat, disp_s).reshape(
            np.shape(outputs["data:aerostructural:aerodynamic:" + comp + ":displacements"])
        )
        outputs["data:aerostructural:aerodynamic:" + comp + ":displacements"] = disp_a
