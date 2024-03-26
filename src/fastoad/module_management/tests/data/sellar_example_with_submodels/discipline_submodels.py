"""Sellar discipline 1"""
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

from math import exp

import openmdao.api as om

from fastoad._utils.sellar.disc1 import BasicDisc1
from fastoad._utils.sellar.disc2 import BasicDisc2
from fastoad._utils.sellar.function_f import BasicFunctionF
from fastoad._utils.sellar.functions_g import BasicFunctionG1, BasicFunctionG2
from fastoad.module_management.service_registry import RegisterSubmodel


@RegisterSubmodel("required_submodel.sellar.disc1", "submodel.sellar.disc1")
class Disc1(BasicDisc1):
    pass


@RegisterSubmodel("required_submodel.sellar.disc1", "submodel.sellar.disc1.alternate")
class AlternateDisc1(BasicDisc1):
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        z1 = inputs["z"][0]
        z2 = inputs["z"][1]
        x1 = inputs["x"]
        y2 = inputs["y2"]

        outputs["y1"] = z1 ** 4 + z2 + x1 - 0.2 * y2


@RegisterSubmodel("required_submodel.sellar.disc2", "submodel.sellar.disc2")
class Disc2(BasicDisc2):
    pass


@RegisterSubmodel("required_submodel.sellar.objective", "submodel.sellar.objective")
class FunctionF(BasicFunctionF):
    pass


@RegisterSubmodel("required_submodel.sellar.objective", "submodel.sellar.objective.alternate")
class AlternateFunctionF(BasicFunctionF):
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        z2 = inputs["z"][1]
        x1 = inputs["x"]
        y1 = inputs["y1"]
        y2 = inputs["y2"]

        outputs["f"] = x1 ** 2 + z2 + y1 + 0.5 * exp(-y2)


@RegisterSubmodel("required_submodel.sellar.constraints", "submodel.sellar.constraints")
class Constraints(om.Group):
    def setup(self):
        self.add_subsystem("function_g1", BasicFunctionG1(), promotes=["*"])
        self.add_subsystem("function_g2", BasicFunctionG2(), promotes=["*"])


@RegisterSubmodel("required_submodel.sellar.constraint2", "submodel.sellar.constraint2")
class FunctionG2(BasicFunctionG2):
    pass
