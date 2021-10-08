"""Computation of max CL in landing conditions."""
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

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent

from fastoad.module_management.service_registry import RegisterSubmodel
from ..constants import SERVICE_LANDING_MAX_CL


@RegisterSubmodel(SERVICE_LANDING_MAX_CL, "fastoad.submodel.aerodynamics.landing.max_CL.legacy")
class ComputeMaxClLanding(ExplicitComponent):
    """Computation of max CL in landing conditions."""

    def setup(self):
        self.add_input("data:aerodynamics:aircraft:landing:CL_max_clean", val=np.nan)
        self.add_input("data:aerodynamics:high_lift_devices:landing:CL", val=np.nan)
        self.add_input(
            "tuning:aerodynamics:aircraft:landing:CL_max:landing_gear_effect:k", val=np.nan
        )
        self.add_output("data:aerodynamics:aircraft:landing:CL_max")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        cl_max_clean = inputs["data:aerodynamics:aircraft:landing:CL_max_clean"]
        cl_max_landing = cl_max_clean + inputs["data:aerodynamics:high_lift_devices:landing:CL"]
        cl_max_landing = (
            cl_max_landing
            * inputs["tuning:aerodynamics:aircraft:landing:CL_max:landing_gear_effect:k"]
        )

        outputs["data:aerodynamics:aircraft:landing:CL_max"] = cl_max_landing
