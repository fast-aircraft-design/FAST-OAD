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

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.update_mtow")
class UpdateMTOW(om.ExplicitComponent):
    """
    Computes new mtow based on the mission fuel and structural weight from previous iteration
    """

    def setup(self):
        # Defining the input(s)

        self.add_input(name="owe", units="kg", val=np.nan)
        self.add_input(name="payload", units="kg", val=np.nan)
        self.add_input(name="mission_fuel", units="kg", val=np.nan)

        # Defining the output(s)

        self.add_output(name="mtow", val=500.0, units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        # Assigning the input to local variable for clarity
        owe = inputs["owe"]
        payload = inputs["payload"]
        mission_fuel = inputs["mission_fuel"]

        # Let's simply add the weight we computed
        mtow_new = owe + payload + mission_fuel

        outputs["mtow"] = mtow_new
