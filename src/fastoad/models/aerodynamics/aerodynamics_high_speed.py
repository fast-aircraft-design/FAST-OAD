"""Computation of aerodynamic polar in cruise conditions."""
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
from .constants import (
    SERVICE_CD0,
    SERVICE_CD_COMPRESSIBILITY,
    SERVICE_CD_TRIM,
    SERVICE_INDUCED_DRAG_COEFFICIENT,
    SERVICE_INITIALIZE_CL,
    SERVICE_OSWALD_COEFFICIENT,
    SERVICE_POLAR,
    SERVICE_REYNOLDS_COEFFICIENT,
)


@RegisterOpenMDAOSystem("fastoad.aerodynamics.highspeed.legacy", domain=ModelDomain.AERODYNAMICS)
class AerodynamicsHighSpeed(om.Group):
    """
    Computes aerodynamic polar of the aircraft in cruise conditions.

    Drag contributions of each part of the aircraft are computed though analytical
    models.
    """

    def setup(self):
        self.add_subsystem(
            "compute_oswald_coeff",
            RegisterSubmodel.get_submodel(SERVICE_OSWALD_COEFFICIENT),
            promotes=["*"],
        )
        self.add_subsystem(
            "compute_induced_drag_coeff",
            RegisterSubmodel.get_submodel(SERVICE_INDUCED_DRAG_COEFFICIENT),
            promotes=["*"],
        )
        self.add_subsystem(
            "comp_re", RegisterSubmodel.get_submodel(SERVICE_REYNOLDS_COEFFICIENT), promotes=["*"]
        )
        self.add_subsystem(
            "initialize_cl", RegisterSubmodel.get_submodel(SERVICE_INITIALIZE_CL), promotes=["*"]
        )
        self.add_subsystem("cd0_wing", RegisterSubmodel.get_submodel(SERVICE_CD0), promotes=["*"])
        self.add_subsystem(
            "cd_comp", RegisterSubmodel.get_submodel(SERVICE_CD_COMPRESSIBILITY), promotes=["*"]
        )
        self.add_subsystem(
            "cd_trim", RegisterSubmodel.get_submodel(SERVICE_CD_TRIM), promotes=["*"]
        )
        self.add_subsystem(
            "get_polar", RegisterSubmodel.get_submodel(SERVICE_POLAR), promotes=["*"]
        )
