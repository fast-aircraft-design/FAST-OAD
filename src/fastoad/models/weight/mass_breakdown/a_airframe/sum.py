"""Computation of airframe mass."""
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

from fastoad.module_management.service_registry import RegisterSubmodel
from .constants import (
    SERVICE_EMPENNAGE_WEIGHT,
    SERVICE_FLIGHT_CONTROLS_WEIGHT,
    SERVICE_FUSELAGE_WEIGHT,
    SERVICE_LANDING_GEARS_WEIGHT,
    SERVICE_PAINT_WEIGHT,
    SERVICE_PYLONS_WEIGHT,
    SERVICE_WING_WEIGHT,
)
from ..constants import SERVICE_AIRFRAME_WEIGHT
from ..cs25 import Loads


@RegisterSubmodel(SERVICE_AIRFRAME_WEIGHT, "fastoad.submodel.weight.mass_breakdown.airframe.legacy")
class AirframeWeight(om.Group):
    """
    Computes mass of airframe.
    """

    def setup(self):
        # Airframe
        self.add_subsystem("loads", Loads(), promotes=["*"])
        self.add_subsystem(
            "wing_weight", RegisterSubmodel.get_submodel(SERVICE_WING_WEIGHT), promotes=["*"]
        )
        self.add_subsystem(
            "fuselage_weight",
            RegisterSubmodel.get_submodel(SERVICE_FUSELAGE_WEIGHT),
            promotes=["*"],
        )
        self.add_subsystem(
            "empennage_weight",
            RegisterSubmodel.get_submodel(SERVICE_EMPENNAGE_WEIGHT),
            promotes=["*"],
        )
        self.add_subsystem(
            "flight_controls_weight",
            RegisterSubmodel.get_submodel(SERVICE_FLIGHT_CONTROLS_WEIGHT),
            promotes=["*"],
        )
        self.add_subsystem(
            "landing_gear_weight",
            RegisterSubmodel.get_submodel(SERVICE_LANDING_GEARS_WEIGHT),
            promotes=["*"],
        )
        self.add_subsystem(
            "pylons_weight", RegisterSubmodel.get_submodel(SERVICE_PYLONS_WEIGHT), promotes=["*"]
        )
        self.add_subsystem(
            "paint_weight", RegisterSubmodel.get_submodel(SERVICE_PAINT_WEIGHT), promotes=["*"]
        )

        weight_sum = om.AddSubtractComp()
        weight_sum.add_equation(
            "data:weight:airframe:mass",
            [
                "data:weight:airframe:wing:mass",
                "data:weight:airframe:fuselage:mass",
                "data:weight:airframe:horizontal_tail:mass",
                "data:weight:airframe:vertical_tail:mass",
                "data:weight:airframe:flight_controls:mass",
                "data:weight:airframe:landing_gear:main:mass",
                "data:weight:airframe:landing_gear:front:mass",
                "data:weight:airframe:pylon:mass",
                "data:weight:airframe:paint:mass",
            ],
            units="kg",
            desc="Mass of airframe",
        )

        self.add_subsystem(
            "airframe_weight_sum", weight_sum, promotes=["*"],
        )
