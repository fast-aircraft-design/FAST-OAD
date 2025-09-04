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
import scipy.constants as sc


class ComputeFuelMass(om.ExplicitComponent):
    """
    Computes the fuel consumed during the mission based on the Breguet's range equation
    """

    def setup(self):
        # Defining the input(s)

        self.add_input(name="owe", units="kg", val=np.nan)
        self.add_input(name="payload", units="kg", val=np.nan)
        self.add_input(name="mission_range", units="m", val=np.nan)
        self.add_input(name="tsfc", units="kg/N/s", val=np.nan)
        self.add_input(name="l_d_ratio", val=np.nan)
        self.add_input(name="cruise_speed", units="m/s", val=np.nan)

        # Defining the output(s)

        self.add_output(name="mission_fuel", units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        # Assigning the input to local variable for clarity
        owe = inputs["owe"]
        payload = inputs["payload"]
        mission_range = inputs["mission_range"]
        tsfc = inputs["tsfc"]
        l_d = inputs["l_d_ratio"]
        cruise_speed = inputs["cruise_speed"]

        # To simplify the computation, we will first start by computing the range parameter,
        # which correspond to the term inside the exponential in the original formula
        range_parameter = (mission_range * tsfc * sc.g) / (cruise_speed * l_d)

        # Let's now computed the fuel using Breguet's range equation rearranged
        mission_fuel = (owe + payload) * (np.exp(range_parameter) - 1.0)

        outputs["mission_fuel"] = mission_fuel
