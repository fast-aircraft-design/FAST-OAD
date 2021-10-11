"""Computation of aerodynamic polar in low speed conditions."""
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
    PolarType,
    SERVICE_CD0,
    SERVICE_CD_TRIM,
    SERVICE_INDUCED_DRAG_COEFFICIENT,
    SERVICE_INITIALIZE_CL,
    SERVICE_OSWALD_COEFFICIENT,
    SERVICE_POLAR,
    SERVICE_REYNOLDS_COEFFICIENT,
    SERVICE_LOW_SPEED_CL_AOA,
)


@RegisterOpenMDAOSystem("fastoad.aerodynamics.lowspeed.legacy", domain=ModelDomain.AERODYNAMICS)
class AerodynamicsLowSpeed(om.Group):
    """
    Models for low speed aerodynamics
    """

    def setup(self):
        low_speed_option = {"low_speed_aero": True}

        self.add_subsystem(
            "compute_low_speed_aero",
            RegisterSubmodel.get_submodel(SERVICE_LOW_SPEED_CL_AOA),
            promotes=["*"],
        )
        ivc = om.IndepVarComp("data:aerodynamics:aircraft:takeoff:mach", val=0.2)
        self.add_subsystem("mach_low_speed", ivc, promotes=["*"])

        self.add_subsystem(
            "compute_oswald_coeff",
            RegisterSubmodel.get_submodel(SERVICE_OSWALD_COEFFICIENT, low_speed_option),
            promotes=["*"],
        )
        self.add_subsystem(
            "compute_induced_drag_coeff",
            RegisterSubmodel.get_submodel(SERVICE_INDUCED_DRAG_COEFFICIENT, low_speed_option),
            promotes=["*"],
        )
        self.add_subsystem(
            "comp_re",
            RegisterSubmodel.get_submodel(SERVICE_REYNOLDS_COEFFICIENT, low_speed_option),
            promotes=["*"],
        )
        self.add_subsystem(
            "initialize_cl",
            RegisterSubmodel.get_submodel(SERVICE_INITIALIZE_CL, low_speed_option),
            promotes=["*"],
        )
        self.add_subsystem(
            "cd0_wing", RegisterSubmodel.get_submodel(SERVICE_CD0, low_speed_option), promotes=["*"]
        )
        self.add_subsystem(
            "cd_trim",
            RegisterSubmodel.get_submodel(SERVICE_CD_TRIM, low_speed_option),
            promotes=["*"],
        )
        polar_type_option = {"polar_type": PolarType.LOW_SPEED}
        self.add_subsystem(
            "get_polar",
            RegisterSubmodel.get_submodel(SERVICE_POLAR, polar_type_option),
            promotes=["*"],
        )
