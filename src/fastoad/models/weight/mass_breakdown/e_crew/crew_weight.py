"""
Estimation of crew weight
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
import openmdao.api as om

from fastoad.models.weight.mass_breakdown.constants import SERVICE_CREW_MASS
from fastoad.module_management.service_registry import RegisterSubmodel


@RegisterSubmodel(SERVICE_CREW_MASS, "fastoad.submodel.weight.mass.crew.legacy")
class CrewWeight(om.ExplicitComponent):
    """
    Weight estimation for aircraft crew

    Based on :cite:`supaero:2014`, mass contribution E
    """

    def setup(self):
        self.add_input("data:geometry:cabin:crew_count:technical", val=np.nan)
        self.add_input("data:geometry:cabin:crew_count:commercial", val=np.nan)

        self.add_output("data:weight:crew:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        cockpit_crew = inputs["data:geometry:cabin:crew_count:technical"]
        cabin_crew = inputs["data:geometry:cabin:crew_count:commercial"]

        outputs["data:weight:crew:mass"] = 85 * cockpit_crew + 75 * cabin_crew
