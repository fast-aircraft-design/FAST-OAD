"""Sellar openMDAO group"""
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

from fastoad._utils.sellar.sellar_base import BasicSellarModel, GenericSellarFactory, ISellarFactory

from .disc1 import Disc1
from .disc2 import Disc2
from .functions import FunctionF, FunctionG1, FunctionG2


class SellarModel(BasicSellarModel):
    """An OpenMDAO base component to encapsulate Sellar MDA"""

    def initialize(self):
        super().initialize()
        self.options["sellar_factory"] = GenericSellarFactory(
            disc1_class=Disc1,
            disc2_class=Disc2,
            f_class=FunctionF,
            g1_class=FunctionG1,
            g2_class=FunctionG2,
        )

    def setup(self):
        sellar_factory: ISellarFactory = self.options["sellar_factory"]

        indeps = self.add_subsystem("indeps", om.IndepVarComp(), promotes=["*"])
        indeps.add_output("x", 2)
        self.add_subsystem("disc1", sellar_factory.create_disc1(), promotes=["x", "z", "y2"])
        self.add_subsystem("disc2", sellar_factory.create_disc2(), promotes=["z", "y2"])
        self.add_subsystem(
            "objective",
            sellar_factory.create_objective_function(),
            promotes=["x", "z", "y2", "f"],
        )
        self.add_subsystem(
            "constraints", sellar_factory.create_constraints(), promotes=["y2", "g1", "g2"]
        )

        self.connect(
            "disc1.y1", ["disc2.y1", "objective.y1", "constraints.y1"]
        )  # Need for a non-promoted variable
