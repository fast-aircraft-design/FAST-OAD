#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory

from .disc1 import Disc1
from .disc2 import Disc2
from .functions import Functions

# This module makes components available through OpenMDAOSystemFactory
OpenMDAOSystemFactory.register_system(Disc1(), {"Number": 1, "Discipline": "generic", "AnyProp": "Something"})
OpenMDAOSystemFactory.register_system(Disc2(), {"Number": 2, "Discipline": "generic"})
OpenMDAOSystemFactory.register_system(Functions(), {"Discipline": "function"})
