"""
This module compute needed beam section second moment of area given a target deflection, force and
material properties.
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


@oad.RegisterOpenMDAOSystem("fastoad.beam_problem.disp")
class Displacements(om.ExplicitComponent):
    def setup(self):

        self.add_input("data:beam_problem:geometry:L", val=np.nan, desc="beam length", units="m")
        self.add_input(
            "data:beam_problem:material:E", val=np.nan, desc="material Young's modulus", units="Pa"
        )
        self.add_input(
            "data:beam_problem:forces:F",
            val=np.nan,
            desc="force applied at beam extremity",
            units="N",
        )
        self.add_input(
            "data:beam_problem:weight:linear_weight",
            np.nan,
            desc="beam linear weight",
            units="kg/m",
        )
        self.add_input(
            "data:beam_problem:displacements:target",
            np.nan,
            desc="target beam tip deflection",
            units="m",
        )

        self.add_output(
            "data:beam_problem:geometry:Ixx",
            val=1e-5,
            desc="Section second moment of area along w.r.t. x axis",
            units="m**4",
        )

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):

        L = inputs["data:beam_problem:geometry:L"]
        E = inputs["data:beam_problem:material:E"]
        F = inputs["data:beam_problem:forces:F"]
        w = inputs["data:beam_problem:weight:linear_weight"]
        v = inputs["data:beam_problem:displacements:target"]

        outputs["data:beam_problem:geometry:Ixx"] = L ** 3 * (F / 3 - w * L / 8) / (E * v)
