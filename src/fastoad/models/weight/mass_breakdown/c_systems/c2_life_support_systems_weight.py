"""
Estimation of life support systems weight
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

from fastoad.constants import RangeCategory
from fastoad.module_management.service_registry import RegisterSubmodel
from .constants import SERVICE_LIFE_SUPPORT_SYSTEMS_MASS


@RegisterSubmodel(
    SERVICE_LIFE_SUPPORT_SYSTEMS_MASS, "fastoad.submodel.weight.mass.systems.life_support.legacy"
)
class LifeSupportSystemsWeight(om.ExplicitComponent):
    """
    Weight estimation for life support systems

    This includes:

    - insulation
    - air conditioning / pressurization
    - de-icing
    - internal lighting system
    - seats and installation of crew
    - fixed oxygen
    - permanent security kits

    Based on formulas in :cite:`supaero:2014`, mass contribution C2
    """

    def setup(self):
        self.add_input("data:TLAR:range", val=np.nan, units="NM")
        self.add_input("data:geometry:fuselage:maximum_width", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan, units="m")
        self.add_input("data:geometry:cabin:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:sweep_0", val=np.nan, units="rad")
        self.add_input("data:geometry:propulsion:nacelle:diameter", val=np.nan, units="m")
        self.add_input("data:geometry:propulsion:engine:count", val=np.nan)
        self.add_input("data:geometry:cabin:NPAX1", val=np.nan)
        self.add_input("data:geometry:cabin:crew_count:technical", val=np.nan)
        self.add_input("data:geometry:cabin:crew_count:commercial", val=np.nan)
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")
        self.add_input("data:weight:propulsion:engine:mass", val=np.nan, units="kg")
        self.add_input("tuning:weight:systems:life_support:insulation:mass:k", val=1.0)
        self.add_input(
            "tuning:weight:systems:life_support:insulation:mass:offset", val=0.0, units="kg"
        )
        self.add_input("tuning:weight:systems:life_support:air_conditioning:mass:k", val=1.0)
        self.add_input(
            "tuning:weight:systems:life_support:air_conditioning:mass:offset", val=0.0, units="kg"
        )
        self.add_input("tuning:weight:systems:life_support:de-icing:mass:k", val=1.0)
        self.add_input(
            "tuning:weight:systems:life_support:de-icing:mass:offset", val=0.0, units="kg"
        )
        self.add_input("tuning:weight:systems:life_support:cabin_lighting:mass:k", val=1.0)
        self.add_input(
            "tuning:weight:systems:life_support:cabin_lighting:mass:offset", val=0.0, units="kg"
        )
        self.add_input(
            "tuning:weight:systems:life_support:seats_crew_accommodation:mass:k", val=1.0
        )
        self.add_input(
            "tuning:weight:systems:life_support:seats_crew_accommodation:mass:offset",
            val=0.0,
            units="kg",
        )
        self.add_input("tuning:weight:systems:life_support:oxygen:mass:k", val=1.0)
        self.add_input("tuning:weight:systems:life_support:oxygen:mass:offset", val=0.0, units="kg")
        self.add_input("tuning:weight:systems:life_support:safety_equipment:mass:k", val=1.0)
        self.add_input(
            "tuning:weight:systems:life_support:safety_equipment:mass:offset", val=0.0, units="kg"
        )

        self.add_output("data:weight:systems:life_support:insulation:mass", units="kg")
        self.add_output("data:weight:systems:life_support:air_conditioning:mass", units="kg")
        self.add_output("data:weight:systems:life_support:de-icing:mass", units="kg")
        self.add_output("data:weight:systems:life_support:cabin_lighting:mass", units="kg")
        self.add_output(
            "data:weight:systems:life_support:seats_crew_accommodation:mass", units="kg"
        )
        self.add_output("data:weight:systems:life_support:oxygen:mass", units="kg")
        self.add_output("data:weight:systems:life_support:safety_equipment:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        tlar_range = inputs["data:TLAR:range"]
        width_max = inputs["data:geometry:fuselage:maximum_width"]
        height_max = inputs["data:geometry:fuselage:maximum_height"]
        cabin_length = inputs["data:geometry:cabin:length"]
        sweep_leading_edge = inputs["data:geometry:wing:sweep_0"]
        n_engines = inputs["data:geometry:propulsion:engine:count"]
        span = inputs["data:geometry:wing:span"]
        nacelle_diameter = inputs["data:geometry:propulsion:nacelle:diameter"]
        npax1 = inputs["data:geometry:cabin:NPAX1"]
        weight_engines = inputs["data:weight:propulsion:engine:mass"]
        cabin_crew = inputs["data:geometry:cabin:crew_count:commercial"]
        cockpit_crew = inputs["data:geometry:cabin:crew_count:technical"]
        k_c21 = inputs["tuning:weight:systems:life_support:insulation:mass:k"]
        offset_c21 = inputs["tuning:weight:systems:life_support:insulation:mass:offset"]
        k_c22 = inputs["tuning:weight:systems:life_support:air_conditioning:mass:k"]
        offset_c22 = inputs["tuning:weight:systems:life_support:air_conditioning:mass:offset"]
        k_c23 = inputs["tuning:weight:systems:life_support:de-icing:mass:k"]
        offset_c23 = inputs["tuning:weight:systems:life_support:de-icing:mass:offset"]
        k_c24 = inputs["tuning:weight:systems:life_support:cabin_lighting:mass:k"]
        offset_c24 = inputs["tuning:weight:systems:life_support:cabin_lighting:mass:offset"]
        k_c25 = inputs["tuning:weight:systems:life_support:seats_crew_accommodation:mass:k"]
        offset_c25 = inputs[
            "tuning:weight:systems:life_support:seats_crew_accommodation:mass:offset"
        ]
        k_c26 = inputs["tuning:weight:systems:life_support:oxygen:mass:k"]
        offset_c26 = inputs["tuning:weight:systems:life_support:oxygen:mass:offset"]
        k_c27 = inputs["tuning:weight:systems:life_support:safety_equipment:mass:k"]
        offset_c27 = inputs["tuning:weight:systems:life_support:safety_equipment:mass:offset"]

        fuselage_diameter = np.sqrt(width_max * height_max)

        # Mass of insulating system
        temp_c21 = 9.3 * fuselage_diameter * cabin_length
        outputs["data:weight:systems:life_support:insulation:mass"] = k_c21 * temp_c21 + offset_c21

        # Mass of air conditioning and pressurization system
        if tlar_range <= RangeCategory.MEDIUM.max():
            temp_c22 = (
                200
                + 27 * npax1 ** 0.46
                + 7.2 * (n_engines ** 0.7) * (npax1 ** 0.64)
                + npax1
                + 0.0029 * npax1 ** 1.64
            )
        else:
            temp_c22 = (
                450
                + 51 * npax1 ** 0.46
                + 7.2 * (n_engines ** 0.7) * (npax1 ** 0.64)
                + npax1
                + 0.0029 * npax1 ** 1.64
            )
        outputs["data:weight:systems:life_support:air_conditioning:mass"] = (
            k_c22 * temp_c22 + offset_c22
        )

        # Mass of de-icing system
        temp_c23 = (
            53
            + 9.5 * nacelle_diameter * n_engines
            + 1.9 * (span - width_max) / np.cos(sweep_leading_edge)
        )
        outputs["data:weight:systems:life_support:de-icing:mass"] = k_c23 * temp_c23 + offset_c23

        # Mass of internal lighting system
        temp_c24 = 1.4 * cabin_length * fuselage_diameter
        outputs["data:weight:systems:life_support:cabin_lighting:mass"] = (
            k_c24 * temp_c24 + offset_c24
        )

        # Mass of seats and installation system
        temp_c25 = 27 * cockpit_crew + 18 * cabin_crew
        outputs["data:weight:systems:life_support:seats_crew_accommodation:mass"] = (
            k_c25 * temp_c25 + offset_c25
        )

        # Mass of fixed oxygen
        temp_c26 = 80 + 1.3 * npax1
        outputs["data:weight:systems:life_support:oxygen:mass"] = k_c26 * temp_c26 + offset_c26

        # Mass of permanent security kits
        temp_c27 = 0.01 * weight_engines + 2.30 * npax1
        outputs["data:weight:systems:life_support:safety_equipment:mass"] = (
            k_c27 * temp_c27 + offset_c27
        )
