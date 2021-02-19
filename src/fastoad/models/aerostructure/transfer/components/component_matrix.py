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
from .interpolation import InterpolationMatrix


class ComponentMatrix(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("interpolation_method", types=str, default="linear")
        self.options.declare("number_of_sections", types=int)
        self.options.declare("component", types=str)

    def setup(self):
        n_sects = self.options["number_of_sections"]
        comp = self.options["component"]
        if comp in ["wing", "horizontal_tail", "strut"]:
            k = 2
        else:
            k = 1
        s_1 = (n_sects + 1) * k * 3  # number of aerodynamic displacements for symmetric wing
        s_2 = (n_sects + 1) * k * 6  # number of structural displacements for symmetric wing

        #  Fuselage modelling in AVL based on 12 leading edge points no longitudinal discretization
        if comp == "fuselage":
            s_1 = 36
        self.add_input(
            "data:aerostructural:aerodynamic:" + comp + ":nodes", val=np.nan, shape_by_conn=True
        )
        self.add_input(
            "data:aerostructural:structure:" + comp + ":nodes", val=np.nan, shape_by_conn=True
        )
        self.add_output(
            "data:aerostructural:transfer:" + comp + ":matrix", val=0.0, shape=(s_1, s_2)
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        comp = self.options["component"]
        meth = self.options["interpolation_method"]
        nodes_a = inputs["data:aerostructural:aerodynamic:" + comp + ":nodes"]
        nodes_s = inputs["data:aerostructural:structure:" + comp + ":nodes"]
        t_mat = InterpolationMatrix(nodes_a, nodes_s, methode=meth)
        outputs[
            "data:aerostructural:transfer:" + comp + ":matrix"
        ] = t_mat.get_interpolation_matrix()
