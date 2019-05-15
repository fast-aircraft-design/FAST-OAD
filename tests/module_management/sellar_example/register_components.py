#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastoad.module_management.bundle_loader import Loader
from fastoad.module_management.constants import SERVICE_OPENMDAO_SYSTEM

from .disc1 import Disc1
from .disc2 import Disc2

loader = Loader()
loader.context.register_service(SERVICE_OPENMDAO_SYSTEM, Disc1(),
                                {"Number": 1, "Discipline": "generic", "AnyProp": "Something"})
loader.context.register_service(SERVICE_OPENMDAO_SYSTEM, Disc2(),
                                {"Number": 2, "Discipline": "generic"})
