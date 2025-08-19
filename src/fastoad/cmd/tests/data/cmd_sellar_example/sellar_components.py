"""
Registered Sellar components
"""

import numpy as np
import openmdao.api as om

from fastoad._utils.sellar.disc1 import BasicDisc1
from fastoad._utils.sellar.disc2 import BasicDisc2
from fastoad._utils.sellar.function_f import BasicFunctionF
from fastoad._utils.sellar.functions_g import BasicFunctionG1, BasicFunctionG2
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("cmd_test.sellar.disc1")
class RegisteredDisc1(BasicDisc1):
    def setup(self):
        self.add_input(
            "x", val=np.nan, desc="input x"
        )  # NaN as default for testing connexion check
        self.add_input(
            "z", val=[5, 2], desc="variable z", units="m**2"
        )  # for testing non-None units
        self.add_input("y2", val=1.0, desc="variable y2")  # for testing input description capture

        self.add_output("y1", val=1.0, desc="variable y1")  # for testing output description capture


@RegisterOpenMDAOSystem("cmd_test.sellar.disc2")
class RegisteredDisc2(BasicDisc2):
    def setup(self):
        self.add_input("z", val=[5, 2], desc="", units="m**2")  # for testing non-None units
        self.add_input("y1", val=1.0, desc="")

        self.add_output("y2", val=1.0, desc="")


class NewFunctionF(BasicFunctionF):
    def setup(self):
        self.add_input("x", val=2, desc="")
        self.add_input(
            "z", val=[np.nan, np.nan], desc="", units="m**2"
        )  # NaN as default for testing connexion check
        self.add_input("y1", val=1.0, desc="")
        self.add_input("y2", val=1.0, desc="")

        self.add_output("f", val=1.0, desc="Objective")


@RegisterOpenMDAOSystem("cmd_test.sellar.functions")
class Functions(om.Group):
    def setup(self):
        self.add_subsystem("f", NewFunctionF(), promotes=["*"])
        self.add_subsystem("g1", BasicFunctionG1(), promotes=["*"])
        self.add_subsystem("g2", BasicFunctionG2(), promotes=["*"])
