"""Sellar functions"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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


class BasicFunctionG1(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def setup(self):
        self.add_input("y1", val=1.0)
        self.add_output("g1", val=1.0)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""
        y1 = inputs["y1"]
        outputs["g1"] = 3.16 - y1


class BasicFunctionG2(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def setup(self):
        self.add_input("y2", val=1.0, desc="")
        self.add_output("g2", val=1.0, desc="")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""
        y2 = inputs["y2"]
        outputs["g2"] = y2 - 24.0
