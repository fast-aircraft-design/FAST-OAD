# This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
# Copyright (c) 2025 ONERA & ISAE-SUPAERO
# FAST-OAD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np
import openmdao.api as om


class ComputeOwe(om.ExplicitComponent):
    """
    Computes the aircraft structural mass based on its MTOW and wing mass
    """

    def setup(self):
        # Defining the input(s)

        self.add_input(name="mtow", units="kg", val=np.nan)
        self.add_input(name="wing_mass", units="kg", val=np.nan)

        # Defining the output(s)

        self.add_output(name="owe", units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        # Assigning the input to local variable for clarity
        mtow = inputs["mtow"]
        wing_mass = inputs["wing_mass"]

        # Let's start by computing the weight of the aircraft without the wings
        owe_without_wing = mtow * (0.43 + 0.0066 * np.log(mtow))

        # Let's now add the wing mass to get the structural weight
        owe = owe_without_wing + wing_mass

        outputs["owe"] = owe
