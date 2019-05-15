#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastoad.module_management.constants import SERVICE_OPENMDAO_SYSTEM
from pelix.ipopo.decorators import ComponentFactory, Provides, Instantiate, Property

from .disc1 import Disc1


@ComponentFactory("discipline.1.factory")
@Provides(SERVICE_OPENMDAO_SYSTEM)
@Property("Number", value=1)
@Property("Discipline", value="generic")
@Property("AnyProp", value="Something")
@Instantiate("discipline.1.component")
class Disc1Component(Disc1):
    pass
