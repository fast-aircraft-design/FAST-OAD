"""Sellar functions"""

from fastoad._utils.sellar.function_f import BasicFunctionF
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem(
    "module_management_test.sellar.function_f", desc="computation of f", options={"best_doctor": 11}
)
class RegisteredFunctionF(BasicFunctionF):
    def initialize(self):
        self.options.declare("best_doctor", 10)
