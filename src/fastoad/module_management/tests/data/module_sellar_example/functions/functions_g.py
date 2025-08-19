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
