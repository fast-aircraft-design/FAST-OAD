"""
OpenMDAO component for computation of sizing mission.
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("fastoad.mass_performances.compute_MTOW", domain=ModelDomain.OTHER)
class ComputeMTOW(om.AddSubtractComp):
    """
    Computes MTOW from OWE, design payload and consumed fuel in sizing mission.
    """

    def setup(self):
        self.add_equation(
            "data:weight:aircraft:MTOW",
            [
                "data:weight:aircraft:OWE",
                "data:weight:aircraft:payload",
                "data:weight:aircraft:sizing_onboard_fuel_at_input_weight",
            ],
            units="kg",
        )
