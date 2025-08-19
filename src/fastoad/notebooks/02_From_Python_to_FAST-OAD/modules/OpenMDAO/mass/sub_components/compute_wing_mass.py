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


class ComputeWingMass(om.ExplicitComponent):
    """
    Computes the wing mass based on the MTOW, its area and aspect ratio
    """

    def setup(self):
        # Defining the input(s)

        self.add_input(name="wing_area", units="ft**2", val=np.nan)
        # Notice that here we ask for the wing area in sq. ft as it is the unit we need for the
        # formula, so we won't need to convert the wing area in the proper unit
        self.add_input(name="mtow", units="lbm", val=np.nan)
        # Same for the MTOW
        self.add_input(name="aspect_ratio", val=np.nan)

        # Defining the output(s)

        self.add_output(name="wing_mass", units="lbm")
        # Same situation here, the formula outputs in lbm but if we later want to use it in kg,
        # we will just have to ask for units="kg" and OpenMDAO automatically handles the conversion

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        # Assigning the input to local variable for clarity
        wing_area = inputs["wing_area"]
        aspect_ratio = inputs["aspect_ratio"]
        mtow = inputs["mtow"]

        # Let's now apply the formula
        wing_mass = (
            96.948
            * (
                (5.7 * mtow / 1.0e5) ** 0.65
                * aspect_ratio**0.57
                * (wing_area / 100.0) ** 0.61
                * 2.5
            )
            ** 0.993
        )

        outputs["wing_mass"] = wing_mass
