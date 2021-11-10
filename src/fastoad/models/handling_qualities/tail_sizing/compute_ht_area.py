"""
Estimation of horizontal tail area
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

from stdatm import Atmosphere


class ComputeHTArea(om.ExplicitComponent):
    """
    Computes area of horizontal tail plane

    Area is computed to fulfill aircraft balance requirement at rotation speed
    """

    def setup(self):
        self.add_input("data:geometry:fuselage:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:has_T_tail", val=np.nan)
        self.add_input("data:weight:airframe:landing_gear:main:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:airframe:landing_gear:front:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:aircraft:MTOW", val=np.nan, units="kg")
        self.add_input("settings:weight:aircraft:CG:range", val=0.3)
        self.add_input("settings:weight:airframe:landing_gear:front:weight_ratio", val=0.08)
        self.add_input(
            "settings:geometry:horizontal_tail:position_ratio_on_fuselage",
            val=0.91,
            desc="(does not apply for T-tails) distance to aircraft nose of 25% MAC of "
            "horizontal tail divided by fuselage length",
        )

        self.add_output(
            "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25", units="m", ref=30.0
        )
        self.add_output("data:geometry:horizontal_tail:wetted_area", units="m**2", ref=100.0)
        self.add_output("data:geometry:horizontal_tail:area", units="m**2", ref=50.0)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")
        self.declare_partials(
            "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25",
            ["data:geometry:fuselage:length", "data:geometry:wing:MAC:at25percent:x"],
            method="fd",
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        # Area of HTP is computed so its "lift" can counter the moment of weight
        # on front landing gear w.r.t. main landing gear when the CG is in its
        # most front position.

        tail_type = np.round(inputs["data:geometry:has_T_tail"])
        fuselage_length = inputs["data:geometry:fuselage:length"]
        x_wing_aero_center = inputs["data:geometry:wing:MAC:at25percent:x"]
        x_main_lg = inputs["data:weight:airframe:landing_gear:main:CG:x"]
        x_front_lg = inputs["data:weight:airframe:landing_gear:front:CG:x"]
        mtow = inputs["data:weight:aircraft:MTOW"]
        wing_area = inputs["data:geometry:wing:area"]
        wing_mac = inputs["data:geometry:wing:MAC:length"]
        cg_range = inputs["settings:weight:aircraft:CG:range"]
        front_lg_weight_ratio = inputs["settings:weight:airframe:landing_gear:front:weight_ratio"]
        htp_aero_center_ratio = inputs[
            "settings:geometry:horizontal_tail:position_ratio_on_fuselage"
        ]

        delta_lg = x_main_lg - x_front_lg
        atm = Atmosphere(0.0)
        rho = atm.density
        vspeed = atm.speed_of_sound * 0.2  # assume the corresponding Mach of VR is 0.2

        # Proportion of weight on front landing gear is equal to distance between
        # main landing gear and center of gravity, divided by distance between landing gears.

        # If CG is in the most front position, the distance between main landing gear
        # and center of gravity is:
        distance_cg_to_mlg = front_lg_weight_ratio * delta_lg + wing_mac * cg_range

        # So with this front CG, moment of (weight on front landing gear) w.r.t.
        # main landing gear is:
        m_front_lg = mtow * g * distance_cg_to_mlg

        # Moment coefficient
        pdyn = 0.5 * rho * vspeed ** 2
        cm_front_lg = m_front_lg / (pdyn * wing_area * wing_mac)

        # # CM of MTOW on main landing gear w.r.t 25% wing MAC
        # lever_arm = front_lg_weight_ratio * delta_lg  # lever arm wrt CoG
        # lever_arm += wing_mac * cg_range  # and now wrt 25% wing MAC
        # cm_wheel = mtow * g * lever_arm / (pdyn * wing_area * wing_mac)

        ht_volume_coeff = cm_front_lg

        if tail_type == 1:
            aero_centers_distance = fuselage_length - x_wing_aero_center
            wet_area_coeff = 1.6
        elif tail_type == 0:
            aero_centers_distance = htp_aero_center_ratio * fuselage_length - x_wing_aero_center
            wet_area_coeff = 2.0
        else:
            raise ValueError("Value of data:geometry:has_T_tail can only be 0 or 1")

        htp_area = ht_volume_coeff / aero_centers_distance * wing_area * wing_mac
        wet_area_htp = wet_area_coeff * htp_area

        outputs[
            "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"
        ] = aero_centers_distance
        outputs["data:geometry:horizontal_tail:wetted_area"] = wet_area_htp
        outputs["data:geometry:horizontal_tail:area"] = htp_area
