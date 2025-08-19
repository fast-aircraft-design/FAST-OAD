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

from ...OpenMDAO.aerodynamics.sub_components.compute_induced_drag_coefficient import (
    ComputeInducedDragCoefficient,
)
from ...OpenMDAO.aerodynamics.sub_components.compute_lift_to_drag_ratio import (
    ComputeLiftToDragRatio,
)
from ...OpenMDAO.aerodynamics.sub_components.compute_profile_drag import ComputeProfileDrag


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.aerodynamics")
class ComputeAerodynamics(om.Group):
    def setup(self):
        self.add_subsystem(name="compute_profile_drag", subsys=ComputeProfileDrag(), promotes=["*"])
        self.add_subsystem(
            name="compute_induced_drag", subsys=ComputeInducedDragCoefficient(), promotes=["*"]
        )
        self.add_subsystem(
            name="compute_lift_to_drag", subsys=ComputeLiftToDragRatio(), promotes=["*"]
        )
