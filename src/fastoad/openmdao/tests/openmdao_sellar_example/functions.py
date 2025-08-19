"""Sellar functions"""

import numpy as np

from fastoad._utils.sellar.function_f import BasicFunctionF
from fastoad._utils.sellar.functions_g import BasicFunctionG1, BasicFunctionG2


class FunctionF(BasicFunctionF):
    def setup(self):
        self.add_input("x", val=2, desc="")
        self.add_input(
            "z", val=[np.nan, np.nan], desc="", units="m**2"
        )  # NaN as default for testing connexion check
        self.add_input("y1", val=1.0, desc="")
        self.add_input("y2", val=1.0, desc="")

        self.add_output("f", val=1.0, desc="")


class FunctionG1(BasicFunctionG1):
    def setup(self):
        self.add_input("y1", val=1.0, desc="")
        self.add_output("g1", val=1.0, desc="")


class FunctionG2(BasicFunctionG2):
    def setup(self):
        self.add_input("y2", val=1.0, desc="")
        self.add_output("g2", val=1.0, desc="")
