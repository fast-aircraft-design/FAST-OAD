"""Computation of furniture mass."""
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

from openmdao import api as om

from fastoad.module_management.service_registry import RegisterSubmodel
from .constants import (
    SERVICE_PASSENGER_SEATS_MASS,
    SERVICE_FOOD_WATER_MASS,
    SERVICE_SECURITY_KIT_MASS,
    SERVICE_TOILETS_MASS,
)
from ..constants import SERVICE_FURNITURE_MASS


@RegisterSubmodel(
    SERVICE_FURNITURE_MASS, "fastoad.submodel.weight.mass.furniture.cargo_configuration.legacy"
)
class FurnitureWeight(om.Group):
    """
    Computes mass of furniture.
    """

    def setup(self):
        self.add_subsystem(
            "passenger_seats_weight",
            RegisterSubmodel.get_submodel(SERVICE_PASSENGER_SEATS_MASS),
            promotes=["*"],
        )
        self.add_subsystem(
            "food_water_weight",
            RegisterSubmodel.get_submodel(SERVICE_FOOD_WATER_MASS),
            promotes=["*"],
        )
        self.add_subsystem(
            "security_kit_weight",
            RegisterSubmodel.get_submodel(SERVICE_SECURITY_KIT_MASS, ""),
            promotes=["*"],
        )
        self.add_subsystem(
            "toilets_weight", RegisterSubmodel.get_submodel(SERVICE_TOILETS_MASS), promotes=["*"]
        )

        weight_sum = om.AddSubtractComp()
        weight_sum.add_equation(
            "data:weight:furniture:mass",
            [
                "data:weight:furniture:passenger_seats:mass",
                "data:weight:furniture:food_water:mass",
                "data:weight:furniture:security_kit:mass",
                "data:weight:furniture:toilets:mass",
            ],
            units="kg",
            desc="Mass of aircraft furniture",
        )

        self.add_subsystem("furniture_weight_sum", weight_sum, promotes=["*"])
