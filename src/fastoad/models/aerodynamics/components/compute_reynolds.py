"""Computation of Reynolds number"""
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
from stdatm import AtmosphereSI

from fastoad.module_management.service_registry import RegisterSubmodel
from ..constants import SERVICE_REYNOLDS_COEFFICIENT


@RegisterSubmodel(
    SERVICE_REYNOLDS_COEFFICIENT, "fastoad.submodel.aerodynamics.reynolds_coefficient.legacy"
)
class ComputeReynolds(ExplicitComponent):
    """Computation of Reynolds number"""

    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        if self.options["low_speed_aero"]:
            self.add_input("data:aerodynamics:aircraft:takeoff:mach", val=np.nan)
            self.add_output("data:aerodynamics:wing:low_speed:reynolds")
        else:
            self.add_input("data:TLAR:cruise_mach", val=np.nan)
            self.add_input("data:mission:sizing:main_route:cruise:altitude", val=np.nan, units="m")
            self.add_output("data:aerodynamics:wing:cruise:reynolds")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        if self.options["low_speed_aero"]:
            mach = inputs["data:aerodynamics:aircraft:takeoff:mach"]
            altitude = 0.0
        else:
            mach = inputs["data:TLAR:cruise_mach"]
            altitude = inputs["data:mission:sizing:main_route:cruise:altitude"]

        atm = AtmosphereSI(altitude)
        atm.mach = mach
        reynolds = atm.unitary_reynolds

        if self.options["low_speed_aero"]:
            outputs["data:aerodynamics:wing:low_speed:reynolds"] = reynolds
        else:
            outputs["data:aerodynamics:wing:cruise:reynolds"] = reynolds
