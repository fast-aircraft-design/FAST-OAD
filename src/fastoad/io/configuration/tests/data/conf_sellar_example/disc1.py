"""Sellar discipline 1"""

import numpy as np

from fastoad._utils.sellar.disc1 import BasicDisc1
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("configuration_test.sellar.disc1")
class RegisteredDisc1(BasicDisc1):
    """An OpenMDAO component to encapsulate Disc1 discipline"""

    def initialize(self):
        # These options have no effect and are used for checks
        self.options.declare("dummy_disc1_option", types=dict, default={})
        self.options.declare("dummy_generic_option", types=str, default="")
        self.options.declare("input_file", types=str, default="")

    def setup(self):
        self.add_input("x", val=np.nan, desc="")  # NaN as default for testing connexion check
        self.add_input("z", val=[5, 2], desc="", units="m**2")  # for testing non-None units
        self.add_input("y2", val=1.0, desc="")

        self.add_output("y1", val=1.0, desc="")
