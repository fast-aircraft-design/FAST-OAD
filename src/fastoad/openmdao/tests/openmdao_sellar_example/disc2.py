"""Sellar discipline 2"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np

from fastoad._utils.sellar.disc2 import BasicDisc2


class Disc2(BasicDisc2):
    """An OpenMDAO component to encapsulate Disc2 discipline"""

    def setup(self):
        self.add_input(
            "z", val=[5, 2], desc="variable z", units="m**2"
        )  # for testing non-None units
        self.add_input("y1", val=1.0, desc="")

        self.add_output("y2", val=1.0, desc="")


class Disc2Bis(BasicDisc2):
    """An OpenMDAO component to encapsulate Disc2 discipline"""

    def setup(self):
        self.add_input(
            "z", val=[np.nan, np.nan], desc="variable z", units="m**2"
        )  # for testing non-None units
        self.add_input("y1", val=1.0, desc="")

        self.add_output("y2", val=1.0, desc="")
