"""
Demonstrates how to register components in OpenMDAOSystemFactory
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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

from fastoad import OpenMDAOSystemFactory
from .disc1 import Disc1
from .disc2 import Disc2
from .functions import Functions

OpenMDAOSystemFactory.register_system(Disc1, 'sellar.disc1'
                                      , {'Number': 1
                                          , 'Discipline': 'generic'
                                          , 'AnyProp': 'Something'})
OpenMDAOSystemFactory.register_system(Disc2, 'sellar.disc2'
                                      , {'Number': 2
                                          , 'Discipline': 'generic'})
OpenMDAOSystemFactory.register_system(Functions, 'sellar.functions'
                                      , {'Discipline': 'function'})
