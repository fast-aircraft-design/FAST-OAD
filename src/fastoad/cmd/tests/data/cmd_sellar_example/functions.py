"""Sellar functions"""
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

from math import exp

from fastoad.module_management.service_registry import RegisterOpenMDAOSystem
from .functions_base import FunctionsBase


@RegisterOpenMDAOSystem("cmd_test.sellar.functions", options={"best_doctor": 11})
class Functions(FunctionsBase):
    """ An OpenMDAO component to encapsulate Functions discipline """

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """ Functions computation """

        z2 = inputs["z"][1]
        x1 = inputs["x"]
        y1 = inputs["y1"]
        y2 = inputs["y2"]

        outputs["f"] = x1 ** 2 + z2 + y1 + exp(-y2)
        outputs["g1"] = 3.16 - y1
        outputs["g2"] = y2 - 24.0
