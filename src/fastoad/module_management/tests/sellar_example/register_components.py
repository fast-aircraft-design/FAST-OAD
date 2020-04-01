"""
Demonstrates how to register components in OpenMDAOSystemRegistry
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

from fastoad.module_management import OpenMDAOSystemRegistry
from fastoad.module_management.constants import ModelDomain

from .disc1 import Disc1
from .disc2 import Disc2
from .functions import Functions

OpenMDAOSystemRegistry.register_system(
    Disc1, "sellar.disc1", domain=ModelDomain.OTHER, desc="some text"
)
OpenMDAOSystemRegistry.register_system(
    Disc2, "sellar.disc2", domain=ModelDomain.GEOMETRY,
)
OpenMDAOSystemRegistry.register_system(Functions, "sellar.functions", options={"best_doctor": 11})
