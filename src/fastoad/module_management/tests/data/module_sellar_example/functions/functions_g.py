"""Sellar functions"""

from fastoad._utils.sellar.functions_g import BasicFunctionG1, BasicFunctionG2
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("module_management_test.sellar.function_g1", desc="computation of g1")
class RegisteredFunctionG1(BasicFunctionG1):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def initialize(self):
        self.options.declare("best_doctor", 10)


@RegisterOpenMDAOSystem("module_management_test.sellar.function_g2", desc="computation of g2")
class RegisteredFunctionG2(BasicFunctionG2):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def initialize(self):
        self.options.declare("best_doctor", 10)
