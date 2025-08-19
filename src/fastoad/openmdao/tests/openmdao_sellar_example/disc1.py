"""Sellar discipline 1"""

import numpy as np

from fastoad._utils.sellar.disc1 import BasicDisc1

from ...validity_checker import ValidityDomainChecker


@ValidityDomainChecker({"x": (-1, 1), "z": (0, 10)})  # This validity domain should not apply
class Disc1(BasicDisc1):
    """An OpenMDAO component to encapsulate Disc1 discipline"""

    def setup(self):
        self.add_input(
            "x", val=np.nan, desc="input x"
        )  # NaN as default for testing connexion check
        self.add_input("z", val=[5, 2], desc="", units="m**2")  # for testing non-None units
        self.add_input("y2", val=1.0, desc="variable y2")  # for testing input description capture

        self.add_output("y1", val=1.0, desc="variable y1")  # for testing output description capture


@ValidityDomainChecker({"x": (0, 4)})  # This validity domain should apply in case 1
class Disc1Bis(BasicDisc1):
    """An OpenMDAO component to encapsulate Disc1 discipline"""

    def setup(self):
        self.add_input("x", val=2.0, desc="input x")  # NaN as default for testing connexion check
        self.add_input("z", val=[5, 2], desc="", units="m**2")  # for testing non-None units
        self.add_input("y2", val=1.0, desc="variable y2")  # for testing input description capture

        self.add_output("y1", val=1.0, desc="variable y1")  # for testing output description capture


@ValidityDomainChecker({"x": (0, 1), "z": (0, 1)})  # This validity domain should apply in case 2
class Disc1Ter(Disc1Bis):
    """Same component with different validity domain."""


class Disc1Quater(BasicDisc1):
    """An OpenMDAO component to encapsulate Disc1 discipline"""

    def setup(self):
        self.add_input(
            "x", val=np.nan, desc="input x"
        )  # NaN as default for testing connexion check
        self.add_input(
            "z", val=[np.nan, np.nan], desc="", units="m**2"
        )  # for testing non-None units
        self.add_input("y2", val=1.0, desc="variable y2")  # for testing input description capture

        self.add_output("y1", val=1.0, desc="variable y1")  # for testing output description capture
