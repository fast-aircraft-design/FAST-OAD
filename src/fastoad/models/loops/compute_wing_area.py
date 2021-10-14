"""
Computation of wing area
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
from scipy.constants import g

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("fastoad.loop.wing_area", domain=ModelDomain.OTHER)
class ComputeWingArea(om.Group):
    """
    Computes needed wing area for:
      - having enough lift at required approach speed
      - being able to load enough fuel to achieve the sizing mission
    """

    def setup(self):
        self.add_subsystem("wing_area", _ComputeWingArea(), promotes=["*"])
        self.add_subsystem("constraints", _ComputeWingAreaConstraints(), promotes=["*"])


class _ComputeWingArea(om.ExplicitComponent):
    """Computation of wing area from needed approach speed and mission fuel"""

    def setup(self):
        self.add_input("data:geometry:wing:aspect_ratio", val=np.nan)
        self.add_input("data:geometry:wing:root:thickness_ratio", val=np.nan)
        self.add_input("data:geometry:wing:tip:thickness_ratio", val=np.nan)
        self.add_input("data:weight:aircraft:sizing_block_fuel", val=np.nan, units="kg")
        self.add_input("data:TLAR:approach_speed", val=np.nan, units="m/s")

        self.add_input("data:weight:aircraft:MLW", val=np.nan, units="kg")
        self.add_input("data:aerodynamics:aircraft:landing:CL_max", val=np.nan)

        self.add_output("data:geometry:wing:area", val=100.0, units="m**2")

    def setup_partials(self):
        self.declare_partials("data:geometry:wing:area", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        lambda_wing = inputs["data:geometry:wing:aspect_ratio"]
        root_thickness_ratio = inputs["data:geometry:wing:root:thickness_ratio"]
        tip_thickness_ratio = inputs["data:geometry:wing:tip:thickness_ratio"]
        mfw_mission = inputs["data:weight:aircraft:sizing_block_fuel"]
        wing_area_mission = (
            max(1000.0, mfw_mission - 1570.0)
            / 224
            / lambda_wing ** -0.4
            / (0.6 * root_thickness_ratio + 0.4 * tip_thickness_ratio)
        ) ** (1.0 / 1.5)

        approach_speed = inputs["data:TLAR:approach_speed"]
        mlw = inputs["data:weight:aircraft:MLW"]
        max_CL = inputs["data:aerodynamics:aircraft:landing:CL_max"]
        wing_area_approach = 2 * mlw * g / ((approach_speed / 1.23) ** 2) / (1.225 * max_CL)

        outputs["data:geometry:wing:area"] = np.nanmax([wing_area_mission, wing_area_approach])


class _ComputeWingAreaConstraints(om.ExplicitComponent):
    def setup(self):
        self.add_input("data:weight:aircraft:sizing_block_fuel", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:MFW", val=np.nan, units="kg")

        self.add_input("data:TLAR:approach_speed", val=np.nan, units="m/s")
        self.add_input("data:weight:aircraft:MLW", val=np.nan, units="kg")
        self.add_input("data:aerodynamics:aircraft:landing:CL_max", val=np.nan)
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")

        self.add_output("data:weight:aircraft:additional_fuel_capacity", units="kg")
        self.add_output("data:aerodynamics:aircraft:landing:additional_CL_capacity")

    def setup_partials(self):
        self.declare_partials(
            "data:weight:aircraft:additional_fuel_capacity",
            ["data:weight:aircraft:MFW", "data:weight:aircraft:sizing_block_fuel"],
            method="fd",
        )
        self.declare_partials(
            "data:aerodynamics:aircraft:landing:additional_CL_capacity",
            [
                "data:TLAR:approach_speed",
                "data:weight:aircraft:MLW",
                "data:aerodynamics:aircraft:landing:CL_max",
                "data:geometry:wing:area",
            ],
            method="fd",
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        mfw = inputs["data:weight:aircraft:MFW"]
        mission_fuel = inputs["data:weight:aircraft:sizing_block_fuel"]
        v_approach = inputs["data:TLAR:approach_speed"]
        cl_max = inputs["data:aerodynamics:aircraft:landing:CL_max"]
        mlw = inputs["data:weight:aircraft:MLW"]
        wing_area = inputs["data:geometry:wing:area"]

        outputs["data:weight:aircraft:additional_fuel_capacity"] = mfw - mission_fuel
        outputs["data:aerodynamics:aircraft:landing:additional_CL_capacity"] = cl_max - mlw * g / (
            0.5 * 1.225 * (v_approach / 1.23) ** 2 * wing_area
        )
