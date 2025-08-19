"""Sellar discipline 2"""

from fastoad._utils.sellar.disc2 import BasicDisc2


# @RegisterOpenMDAOSystem("module_management_test.sellar.disc2", domain=ModelDomain.GEOMETRY)
# Instead of being registered with the decorator above, this class is registered
# in register_components.py to test this alternate way
class RegisteredDisc2(BasicDisc2):
    """Disc 2 with delayed registering."""

    def initialize(self):
        self.options.declare("answer", 42)
