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
from .components.cd_trim import CdTrim
from .components.compute_low_speed_aero import ComputeAerodynamicsLowSpeed
from .components.compute_polar import ComputePolar, PolarType
from .constants import (
    SERVICE_CD0_FUSELAGE,
    SERVICE_CD0_HORIZONTAL_TAIL,
    SERVICE_CD0_NACELLES_PYLONS,
    SERVICE_CD0_SUM,
    SERVICE_CD0_VERTICAL_TAIL,
    SERVICE_CD0_WING,
    SERVICE_INDUCED_DRAG_COEFFICIENT,
    SERVICE_INITIALIZE_CL,
    SERVICE_OSWALD_COEFFICIENT,
    SERVICE_REYNOLDS_COEFFICIENT,
)


@RegisterOpenMDAOSystem("fastoad.aerodynamics.lowspeed.legacy", domain=ModelDomain.AERODYNAMICS)
class AerodynamicsLowSpeed(om.Group):
    """
    Models for low speed aerodynamics
    """

    def setup(self):
        options = {"low_speed_aero": True}

        self.add_subsystem("compute_low_speed_aero", ComputeAerodynamicsLowSpeed(), promotes=["*"])
        ivc = om.IndepVarComp("data:aerodynamics:aircraft:takeoff:mach", val=0.2)
        self.add_subsystem("mach_low_speed", ivc, promotes=["*"])
        self.add_subsystem(
            "compute_oswald_coeff",
            RegisterSubmodel.get_submodel(SERVICE_OSWALD_COEFFICIENT, options),
            promotes=["*"],
        )
        self.add_subsystem(
            "compute_induced_drag_coeff",
            RegisterSubmodel.get_submodel(SERVICE_INDUCED_DRAG_COEFFICIENT, options),
            promotes=["*"],
        )
        self.add_subsystem(
            "comp_re",
            RegisterSubmodel.get_submodel(SERVICE_REYNOLDS_COEFFICIENT, options),
            promotes=["*"],
        )
        self.add_subsystem(
            "initialize_cl",
            RegisterSubmodel.get_submodel(SERVICE_INITIALIZE_CL, options),
            promotes=["*"],
        )
        self.add_subsystem(
            "cd0_wing", RegisterSubmodel.get_submodel(SERVICE_CD0_WING, options), promotes=["*"],
        )
        self.add_subsystem(
            "cd0_fuselage",
            RegisterSubmodel.get_submodel(SERVICE_CD0_FUSELAGE, options),
            promotes=["*"],
        )
        self.add_subsystem(
            "cd0_ht",
            RegisterSubmodel.get_submodel(SERVICE_CD0_HORIZONTAL_TAIL, options),
            promotes=["*"],
        )
        self.add_subsystem(
            "cd0_vt",
            RegisterSubmodel.get_submodel(SERVICE_CD0_VERTICAL_TAIL, options),
            promotes=["*"],
        )
        self.add_subsystem(
            "cd0_nac_pylons",
            RegisterSubmodel.get_submodel(SERVICE_CD0_NACELLES_PYLONS, options),
            promotes=["*"],
        )
        self.add_subsystem(
            "cd0_total", RegisterSubmodel.get_submodel(SERVICE_CD0_SUM, options), promotes=["*"]
        )
        self.add_subsystem("cd_trim", CdTrim(low_speed_aero=True), promotes=["*"])
        self.add_subsystem("get_polar", ComputePolar(type=PolarType.LOW_SPEED), promotes=["*"])
