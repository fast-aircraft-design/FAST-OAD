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


import numpy as np
import openmdao.api as om

from scipy.interpolate import interp1d


class ComponentRotations(om.ExplicitComponent):
    def initialize(self):

        self.options.declare("component", types=str)
        self.options.declare("number_of_aerodynamic_sections", types=int)

    def setup(self):
        comp = self.options["component"]
        nb_sections = self.options["number_of_aerodynamic_sections"]

        self.add_input(
            "data:aerostructural:structure:" + comp + ":displacements",
            shape_by_conn=True,
            val=np.nan,
        )
        self.add_input(
            "data:aerostructural:aerodynamic:" + comp + ":nodes", val=np.nan, shape_by_conn=True
        )
        self.add_input(
            "data:aerostructural:structure:" + comp + ":nodes", val=np.nan, shape_by_conn=True
        )

        if comp in ["wing", "horizontal_tail", "strut"]:
            shape_dtwist = (nb_sections + 1) * 2
        else:
            shape_dtwist = nb_sections + 1

        self.add_output(
            "data:aerostructural:aerodynamic:" + comp + ":d_twist",
            units="rad",
            shape=shape_dtwist,
            val=0.0,
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        comp = self.options["component"]

        rotations = inputs["data:aerostructural:structure:" + comp + ":displacements"][:, [4, 5]]
        aero_nodes_y = inputs["data:aerostructural:aerodynamic:" + comp + ":nodes"][:, 1]
        aero_nodes_z = inputs["data:aerostructural:aerodynamic:" + comp + ":nodes"][:, 2]
        struct_nodes_y = inputs["data:aerostructural:structure:" + comp + ":nodes"][:, 1]
        struct_nodes_z = inputs["data:aerostructural:structure:" + comp + ":nodes"][:, 2]

        if comp in ["wing", "horizontal_tail", "strut"]:
            interp_rotation = interp1d(struct_nodes_y, rotations[:, 0])
            dtwist = interp_rotation(aero_nodes_y)

        if comp in ["vertical_tail"]:
            interp_rotation = interp1d(struct_nodes_z, rotations[:, 1])
            dtwist = interp_rotation(aero_nodes_z)

        outputs["data:aerostructural:aerodynamic:" + comp + ":d_twist"] = dtwist
