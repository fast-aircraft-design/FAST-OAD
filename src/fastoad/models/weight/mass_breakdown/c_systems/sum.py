"""Computation of mass of systems."""
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
    SERVICE_POWER_SYSTEMS_MASS,
    SERVICE_LIFE_SUPPORT_SYSTEMS_MASS,
    SERVICE_NAVIGATION_SYSTEMS_MASS,
    SERVICE_TRANSMISSION_SYSTEMS_MASS,
    SERVICE_FIXED_OPERATIONAL_SYSTEMS_MASS,
    SERVICE_FLIGHT_KIT_MASS,
)
from ..constants import SERVICE_SYSTEMS_MASS


@RegisterSubmodel(SERVICE_SYSTEMS_MASS, "fastoad.submodel.weight.mass.systems.legacy")
class SystemsWeight(om.Group):
    """
    Computes mass of systems.
    """

    def setup(self):
        self.add_subsystem(
            "power_systems_weight",
            RegisterSubmodel.get_submodel(SERVICE_POWER_SYSTEMS_MASS),
            promotes=["*"],
        )
        self.add_subsystem(
            "life_support_systems_weight",
            RegisterSubmodel.get_submodel(SERVICE_LIFE_SUPPORT_SYSTEMS_MASS),
            promotes=["*"],
        )
        self.add_subsystem(
            "navigation_systems_weight",
            RegisterSubmodel.get_submodel(SERVICE_NAVIGATION_SYSTEMS_MASS),
            promotes=["*"],
        )
        self.add_subsystem(
            "transmission_systems_weight",
            RegisterSubmodel.get_submodel(SERVICE_TRANSMISSION_SYSTEMS_MASS),
            promotes=["*"],
        )
        self.add_subsystem(
            "fixed_operational_systems_weight",
            RegisterSubmodel.get_submodel(SERVICE_FIXED_OPERATIONAL_SYSTEMS_MASS),
            promotes=["*"],
        )
        self.add_subsystem(
            "flight_kit_weight",
            RegisterSubmodel.get_submodel(SERVICE_FLIGHT_KIT_MASS),
            promotes=["*"],
        )

        weight_sum = om.AddSubtractComp()
        weight_sum.add_equation(
            "data:weight:systems:mass",
            [
                "data:weight:systems:power:auxiliary_power_unit:mass",
                "data:weight:systems:power:electric_systems:mass",
                "data:weight:systems:power:hydraulic_systems:mass",
                "data:weight:systems:life_support:insulation:mass",
                "data:weight:systems:life_support:air_conditioning:mass",
                "data:weight:systems:life_support:de-icing:mass",
                "data:weight:systems:life_support:cabin_lighting:mass",
                "data:weight:systems:life_support:seats_crew_accommodation:mass",
                "data:weight:systems:life_support:oxygen:mass",
                "data:weight:systems:life_support:safety_equipment:mass",
                "data:weight:systems:navigation:mass",
                "data:weight:systems:transmission:mass",
                "data:weight:systems:operational:radar:mass",
                "data:weight:systems:operational:cargo_hold:mass",
                "data:weight:systems:flight_kit:mass",
            ],
            units="kg",
            desc="Mass of aircraft systems",
        )

        self.add_subsystem("systems_weight_sum", weight_sum, promotes=["*"])
