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

import openmdao.api as om

import fastoad.api as oad

from .aerodynamics.aerodynamics import ComputeAerodynamics
from .geometry.geometry import ComputeGeometry
from .mass.mass import ComputeMass
from .performance.performance import ComputePerformance
from .update_mtow.update_mtow import UpdateMTOW


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.global")
class SizingLoopMTOW(om.Group):
    """
    Gather all the discipline module/groups into the main problem
    """

    def setup(self):
        self.add_subsystem(name="compute_geometry", subsys=ComputeGeometry(), promotes=["*"])
        self.add_subsystem(
            name="compute_aerodynamics", subsys=ComputeAerodynamics(), promotes=["*"]
        )
        self.add_subsystem(name="compute_mass", subsys=ComputeMass(), promotes=["*"])
        self.add_subsystem(name="compute_performance", subsys=ComputePerformance(), promotes=["*"])
        self.add_subsystem(name="update_mtow", subsys=UpdateMTOW(), promotes=["*"])
