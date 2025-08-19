"""
Registered Sellar components
"""

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
