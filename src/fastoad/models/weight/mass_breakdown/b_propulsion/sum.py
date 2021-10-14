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

"""Computation of propulsion mass."""
from openmdao import api as om

from fastoad.module_management.service_registry import RegisterSubmodel
from .constants import SERVICE_ENGINE_MASS, SERVICE_FUEL_LINES_MASS, SERVICE_UNCONSUMABLES_MASS
from ..constants import SERVICE_PROPULSION_MASS


@RegisterSubmodel(SERVICE_PROPULSION_MASS, "fastoad.submodel.weight.mass.propulsion.legacy")
class PropulsionWeight(om.Group):
    """
    Computes mass of propulsion.
    """

    def setup(self):
        # Engine have to be computed before pylons
        self.add_subsystem(
            "engines_weight", RegisterSubmodel.get_submodel(SERVICE_ENGINE_MASS), promotes=["*"]
        )
        self.add_subsystem(
            "fuel_lines_weight",
            RegisterSubmodel.get_submodel(SERVICE_FUEL_LINES_MASS),
            promotes=["*"],
        )
        self.add_subsystem(
            "unconsumables_weight",
            RegisterSubmodel.get_submodel(SERVICE_UNCONSUMABLES_MASS),
            promotes=["*"],
        )

        weight_sum = om.AddSubtractComp()
        weight_sum.add_equation(
            "data:weight:propulsion:mass",
            [
                "data:weight:propulsion:engine:mass",
                "data:weight:propulsion:fuel_lines:mass",
                "data:weight:propulsion:unconsumables:mass",
            ],
            units="kg",
            desc="Mass of the propulsion system",
        )

        self.add_subsystem("propulsion_weight_sum", weight_sum, promotes=["*"])
