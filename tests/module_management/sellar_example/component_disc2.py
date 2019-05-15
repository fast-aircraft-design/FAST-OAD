#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastoad.module_management.constants import SERVICE_OPENMDAO_SYSTEM
from pelix.ipopo.decorators import ComponentFactory, Provides, Instantiate, Property

from .disc2 import Disc2


@ComponentFactory("discipline.2.factory")
@Provides(SERVICE_OPENMDAO_SYSTEM)
@Property("Number", value=2)
@Property("Discipline", value="generic")
@Instantiate("discipline.2.component")
class Disc2Component(Disc2):
    pass
