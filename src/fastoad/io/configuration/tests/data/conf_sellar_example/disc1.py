# This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
# Copyright (c) 2025 ONERA & ISAE-SUPAERO
# FAST-OAD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later

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
