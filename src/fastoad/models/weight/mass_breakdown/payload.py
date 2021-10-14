"""
Payload mass computation
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

import numpy as np
from openmdao import api as om

from fastoad.models.weight.mass_breakdown.constants import SERVICE_PAYLOAD_MASS
from fastoad.module_management.service_registry import RegisterSubmodel


@RegisterSubmodel(SERVICE_PAYLOAD_MASS, "fastoad.submodel.weight.mass.payload.legacy")
class ComputePayload(om.ExplicitComponent):
    """Computes payload from NPAX"""

    def setup(self):
        self.add_input("data:TLAR:NPAX", val=np.nan)
        self.add_input(
            "settings:weight:aircraft:payload:design_mass_per_passenger",
            val=90.72,
            units="kg",
            desc="Design value of mass per passenger",
        )
        self.add_input(
            "settings:weight:aircraft:payload:max_mass_per_passenger",
            val=130.72,
            units="kg",
            desc="Maximum value of mass per passenger",
        )

        self.add_output("data:weight:aircraft:payload", units="kg")
        self.add_output("data:weight:aircraft:max_payload", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        npax = inputs["data:TLAR:NPAX"]
        mass_per_pax = inputs["settings:weight:aircraft:payload:design_mass_per_passenger"]
        max_mass_per_pax = inputs["settings:weight:aircraft:payload:max_mass_per_passenger"]

        outputs["data:weight:aircraft:payload"] = npax * mass_per_pax
        outputs["data:weight:aircraft:max_payload"] = npax * max_mass_per_pax
