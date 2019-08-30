# -*- coding: utf-8 -*-
"""
Demonstrates a way to register components in OpenMDAOSystemFactory
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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

from pelix.ipopo.decorators import ComponentFactory, Provides, Property, Instantiate

from fastoad.module_management.constants import SERVICE_OPENMDAO_SYSTEM
from .disc1 import Disc1
from .disc2 import Disc2
from .functions import Functions


## Though service registering is done with decorators, following lines are
## kept to show an alternate way
# OpenMDAOSystemFactory.register_system(Disc1()
#                                       , {"Number": 1
#                                           , "Discipline": "generic"
#                                           , "AnyProp": "Something"})
# OpenMDAOSystemFactory.register_system(Disc2()
#                                       , {"Number": 2
#                                           , "Discipline": "generic"})
# OpenMDAOSystemFactory.register_system(Functions()
#                                       , {"Discipline": "function"})
#

@ComponentFactory("sellar.disc1.factory")
@Provides(SERVICE_OPENMDAO_SYSTEM)
@Property("Number", None, 1)
@Property("Discipline", None, "generic")
@Property("AnyProp", None, "Something")
@Instantiate("disc1")
class Disc1Service(Disc1):
    pass


@ComponentFactory("sellar.disc2.factory")
@Provides(SERVICE_OPENMDAO_SYSTEM)
@Property("Number", None, 2)
@Property("Discipline", None, "generic")
@Instantiate("disc2")
class Disc2Service(Disc2):
    pass


@ComponentFactory("sellar.functions.factory")
@Provides(SERVICE_OPENMDAO_SYSTEM)
@Property("Discipline", None, "function")
@Instantiate("functions")
class FunctionsService(Functions):
    pass
