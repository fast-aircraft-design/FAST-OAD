"""Sellar discipline 2"""

import numpy as np

from fastoad._utils.sellar.disc2 import BasicDisc2


class Disc2(BasicDisc2):
    """An OpenMDAO component to encapsulate Disc2 discipline"""

    def setup(self):
        self.add_input(
            "z", val=[5, 2], desc="variable z", units="m**2"
        )  # for testing non-None units
        self.add_input("y1", val=1.0, desc="")

        # shape_by_conn=True here to be sure it does not create problems
        # in input reading.
        self.add_output("y2", shape_by_conn=True, val=1.0, desc="")


class Disc2Bis(BasicDisc2):
    """An OpenMDAO component to encapsulate Disc2 discipline"""

    def setup(self):
        self.add_input(
            "z", val=[np.nan, np.nan], desc="variable z", units="m**2"
        )  # for testing non-None units
        self.add_input("y1", val=1.0, desc="")

        self.add_output("y2", val=1.0, desc="")
