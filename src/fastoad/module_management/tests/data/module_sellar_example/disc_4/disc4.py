"""Sellar discipline 2"""
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

import openmdao.ap as om

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("module_management_test.sellar.disc4", domain=ModelDomain.GEOMETRY)
class RegisteredDisc4(om.ExplicitComponent):
    """Disc 4 which can be registered but can be used"""

    def setup(self):
        self.add_input("y2", val=1.0)

        self.add_output("y4", val=67.0)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    # pylint: disable=invalid-name
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """
        Evaluates the equation
        y4 = y2 * 67.0
        """

        y2 = inputs["y2"]

        outputs["y4"] = y2 * 67.0
