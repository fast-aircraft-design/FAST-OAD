"""
Registered Sellar components
"""
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

from fastoad._utils.sellar.disc1 import BasicDisc1
from fastoad._utils.sellar.disc2 import BasicDisc2
from fastoad._utils.sellar.function_f import BasicFunctionF
from fastoad._utils.sellar.functions_g import BasicFunctionG1, BasicFunctionG2
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("postproc_test.sellar.disc1")
class Disc1(BasicDisc1):
    pass


@RegisterOpenMDAOSystem("postproc_test.sellar.disc2")
class Disc2(BasicDisc2):
    pass


@RegisterOpenMDAOSystem("postproc_test.sellar.functions")
class Functions(om.Group):
    def setup(self):
        self.add_subsystem("f", BasicFunctionF(), promotes=["*"])
        self.add_subsystem("g1", BasicFunctionG1(), promotes=["*"])
        self.add_subsystem("g2", BasicFunctionG2(), promotes=["*"])
