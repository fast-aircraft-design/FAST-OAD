"""Computation of aerodynamic characteristics at takeoff."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

import openmdao.api as om

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterSubmodel
from .constants import PolarType, SERVICE_POLAR, SERVICE_HIGH_LIFT


@RegisterOpenMDAOSystem("fastoad.aerodynamics.takeoff.legacy", domain=ModelDomain.AERODYNAMICS)
class AerodynamicsTakeoff(om.Group):
    """
    Computes aerodynamic characteristics at takeoff.

    - Computes CL and CD increments due to high-lift devices at takeoff.
    """

    def setup(self):
        landing_flag_option = {"landing_flag": False}
        self.add_subsystem(
            "delta_cl_cd",
            RegisterSubmodel.get_submodel(SERVICE_HIGH_LIFT, landing_flag_option),
            promotes=["*"],
        )

        polar_type_option = {"polar_type": PolarType.TAKEOFF}
        self.add_subsystem(
            "polar", RegisterSubmodel.get_submodel(SERVICE_POLAR, polar_type_option), promotes=["*"]
        )
