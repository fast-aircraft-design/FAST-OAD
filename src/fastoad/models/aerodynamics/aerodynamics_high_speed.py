"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""
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
from .components.cd0_nacelle_pylons import Cd0NacelleAndPylons
from .components.cd0_total import Cd0Total
from .components.cd_compressibility import CdCompressibility
from .components.cd_trim import CdTrim
from .components.compute_polar import ComputePolar
from .constants import (
    SERVICE_OSWALD_COEFFICIENT,
    SERVICE_INDUCED_DRAG_COEFFICIENT,
    SERVICE_REYNOLDS_COEFFICIENT,
    SERVICE_INITIALIZE_CL,
    SERVICE_CD0_WING,
    SERVICE_CD0_FUSELAGE,
    SERVICE_CD0_HORIZONTAL_TAIL,
    SERVICE_CD0_VERTICAL_TAIL,
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
        self.add_subsystem(
            "cd0_wing", RegisterSubmodel.get_submodel(SERVICE_CD0_WING), promotes=["*"]
        )
        self.add_subsystem(
            "cd0_fuselage", RegisterSubmodel.get_submodel(SERVICE_CD0_FUSELAGE), promotes=["*"]
        )
        self.add_subsystem(
            "cd0_ht", RegisterSubmodel.get_submodel(SERVICE_CD0_HORIZONTAL_TAIL), promotes=["*"]
        )
        self.add_subsystem(
            "cd0_vt", RegisterSubmodel.get_submodel(SERVICE_CD0_VERTICAL_TAIL), promotes=["*"]
        )
        self.add_subsystem("cd0_nac_pylons", Cd0NacelleAndPylons(), promotes=["*"])
        self.add_subsystem("cd0_total", Cd0Total(), promotes=["*"])
        self.add_subsystem("cd_comp", CdCompressibility(), promotes=["*"])
        self.add_subsystem("cd_trim", CdTrim(), promotes=["*"])
        self.add_subsystem("get_polar", ComputePolar(), promotes=["*"])
