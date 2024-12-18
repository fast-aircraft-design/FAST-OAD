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

import numpy as np

from fastoad._utils.sellar.function_f import BasicFunctionF
from fastoad._utils.sellar.functions_g import BasicFunctionG1, BasicFunctionG2


class FunctionF(BasicFunctionF):
    def setup(self):
        self.add_input("x", val=2, desc="")
        self.add_input(
            "z", val=[np.nan, np.nan], desc="", units="m**2"
        )  # NaN as default for testing connexion check
        self.add_input("y1", val=1.0, desc="")
        self.add_input("y2", val=1.0, desc="")

        self.add_output("f", val=1.0, desc="")


class FunctionG1(BasicFunctionG1):
    def setup(self):
        self.add_input("y1", val=1.0, desc="")
        self.add_output("g1", val=1.0, desc="")


class FunctionG2(BasicFunctionG2):
    def setup(self):
        self.add_input("y2", val=1.0, desc="")
        self.add_output("g2", val=1.0, desc="")
