"""Sellar discipline 2"""

from fastoad._utils.sellar.disc2 import BasicDisc2
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("configuration_test.sellar.disc2")
class RegisteredDisc2(BasicDisc2):
    """An OpenMDAO component to encapsulate Disc2 discipline"""

    def setup(self):
        self.add_input("z", val=[5, 2], desc="", units="m**2")  # for testing non-None units
        self.add_input("y1", val=1.0, desc="")

        self.add_output("y2", val=1.0, desc="")
