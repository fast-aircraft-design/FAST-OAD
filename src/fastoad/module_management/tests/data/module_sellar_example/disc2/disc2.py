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

"""Sellar discipline 2"""

from fastoad._utils.sellar.disc2 import BasicDisc2


# @RegisterOpenMDAOSystem("module_management_test.sellar.disc2", domain=ModelDomain.GEOMETRY)
# Instead of being registered with the decorator above, this class is registered
# in register_components.py to test this alternate way
class RegisteredDisc2(BasicDisc2):
    """Disc 2 with delayed registering."""

    def initialize(self):
        self.options.declare("answer", 42)
