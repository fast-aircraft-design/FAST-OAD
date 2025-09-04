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

"""Sellar functions"""

from math import exp

import openmdao.api as om


class BasicFunctionF(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def setup(self):
        self.add_input("x", val=2.0)
        self.add_input("z", val=[5.0, 2.0])
        self.add_input("y1", val=1.0)
        self.add_input("y2", val=1.0)

        self.add_output("f", val=1.0)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""

        z2 = inputs["z"][1]
        x1 = inputs["x"].item()
        y1 = inputs["y1"].item()
        y2 = inputs["y2"].item()

        outputs["f"] = x1**2 + z2 + y1 + exp(-y2)
