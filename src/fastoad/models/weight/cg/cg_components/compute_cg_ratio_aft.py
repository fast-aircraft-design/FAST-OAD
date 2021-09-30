"""
    Estimation of center of gravity ratio with aft
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

from fastoad.module_management.service_registry import RegisterSubmodel
from ..constants import SERVICE_EMPTY_AIRCRAFT_CG


@RegisterSubmodel(SERVICE_EMPTY_AIRCRAFT_CG, "fastoad.submodel.weight.cg.empty_aircraft.legacy")
class ComputeCGRatioAft(om.Group):
    def setup(self):
        self.add_subsystem("cg_all", ComputeCG(), promotes=["*"])
        self.add_subsystem("cg_ratio", CGRatio(), promotes=["*"])


class ComputeCG(om.ExplicitComponent):
    def initialize(self):
        self.options.declare(
            "cg_names",
            default=[
                "data:weight:airframe:wing:CG:x",
                "data:weight:airframe:fuselage:CG:x",
                "data:weight:airframe:horizontal_tail:CG:x",
                "data:weight:airframe:vertical_tail:CG:x",
                "data:weight:airframe:flight_controls:CG:x",
                "data:weight:airframe:landing_gear:main:CG:x",
                "data:weight:airframe:landing_gear:front:CG:x",
                "data:weight:airframe:pylon:CG:x",
                "data:weight:airframe:paint:CG:x",
                "data:weight:propulsion:engine:CG:x",
                "data:weight:propulsion:fuel_lines:CG:x",
                "data:weight:propulsion:unconsumables:CG:x",
                "data:weight:systems:power:auxiliary_power_unit:CG:x",
                "data:weight:systems:power:electric_systems:CG:x",
                "data:weight:systems:power:hydraulic_systems:CG:x",
                "data:weight:systems:life_support:insulation:CG:x",
                "data:weight:systems:life_support:air_conditioning:CG:x",
                "data:weight:systems:life_support:de-icing:CG:x",
                "data:weight:systems:life_support:cabin_lighting:CG:x",
                "data:weight:systems:life_support:seats_crew_accommodation:CG:x",
                "data:weight:systems:life_support:oxygen:CG:x",
                "data:weight:systems:life_support:safety_equipment:CG:x",
                "data:weight:systems:navigation:CG:x",
                "data:weight:systems:transmission:CG:x",
                "data:weight:systems:operational:radar:CG:x",
                "data:weight:systems:operational:cargo_hold:CG:x",
                "data:weight:systems:flight_kit:CG:x",
                "data:weight:furniture:passenger_seats:CG:x",
                "data:weight:furniture:food_water:CG:x",
                "data:weight:furniture:security_kit:CG:x",
                "data:weight:furniture:toilets:CG:x",
            ],
        )

        self.options.declare(
            "mass_names",
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
                "data:weight:propulsion:engine:mass",
                "data:weight:propulsion:fuel_lines:mass",
                "data:weight:propulsion:unconsumables:mass",
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
                "data:weight:furniture:passenger_seats:mass",
                "data:weight:furniture:food_water:mass",
                "data:weight:furniture:security_kit:mass",
                "data:weight:furniture:toilets:mass",
            ],
        )

    def setup(self):
        for cg_name in self.options["cg_names"]:
            self.add_input(cg_name, val=np.nan, units="m")
        for mass_name in self.options["mass_names"]:
            self.add_input(mass_name, val=np.nan, units="kg")

        self.add_output("data:weight:aircraft_empty:mass", units="kg")
        self.add_output("data:weight:aircraft_empty:CG:x", units="m")

    def setup_partials(self):
        self.declare_partials("data:weight:aircraft_empty:mass", "*", method="fd")
        self.declare_partials("data:weight:aircraft_empty:CG:x", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        cgs = [inputs[cg_name][0] for cg_name in self.options["cg_names"]]
        masses = [inputs[mass_name][0] for mass_name in self.options["mass_names"]]

        weight_moment = np.dot(cgs, masses)
        outputs["data:weight:aircraft_empty:mass"] = np.sum(masses)
        outputs["data:weight:aircraft_empty:CG:x"] = (
            weight_moment / outputs["data:weight:aircraft_empty:mass"]
        )


class CGRatio(om.ExplicitComponent):
    def setup(self):
        self.add_input("data:weight:aircraft_empty:CG:x", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")

        self.add_output("data:weight:aircraft:empty:CG:MAC_position")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        x_cg_all = inputs["data:weight:aircraft_empty:CG:x"]
        wing_position = inputs["data:geometry:wing:MAC:at25percent:x"]
        mac = inputs["data:geometry:wing:MAC:length"]

        outputs["data:weight:aircraft:empty:CG:MAC_position"] = (
            x_cg_all - wing_position + 0.25 * mac
        ) / mac
