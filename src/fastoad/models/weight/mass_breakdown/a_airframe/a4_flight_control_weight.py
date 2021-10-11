"""
Estimation of flight controls weight
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
from .constants import SERVICE_FLIGHT_CONTROLS_MASS


@RegisterSubmodel(
    SERVICE_FLIGHT_CONTROLS_MASS, "fastoad.submodel.weight.mass.airframe.flight_control.legacy"
)
class FlightControlsWeight(om.ExplicitComponent):
    """
    Flight controls weight estimation

    Based on formulas in :cite:`supaero:2014`, mass contribution A4
    """

    def setup(self):
        self.add_input("data:geometry:fuselage:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:b_50", val=np.nan, units="m")
        self.add_input("data:mission:sizing:cs25:sizing_load_1", val=np.nan, units="kg")
        self.add_input("data:mission:sizing:cs25:sizing_load_2", val=np.nan, units="kg")
        self.add_input(
            "settings:weight:airframe:flight_controls:mass:k_fc", val=0.85
        )  # FIXME: this one should depend on a boolan electric/not-electric flight_controls
        self.add_input("tuning:weight:airframe:flight_controls:mass:k", val=1.0)
        self.add_input("tuning:weight:airframe:flight_controls:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:airframe:flight_controls:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        fus_length = inputs["data:geometry:fuselage:length"]
        b_50 = inputs["data:geometry:wing:b_50"]
        k_fc = inputs["settings:weight:airframe:flight_controls:mass:k_fc"]
        k_a4 = inputs["tuning:weight:airframe:flight_controls:mass:k"]
        offset_a4 = inputs["tuning:weight:airframe:flight_controls:mass:offset"]

        max_nm = max(
            inputs["data:mission:sizing:cs25:sizing_load_1"],
            inputs["data:mission:sizing:cs25:sizing_load_2"],
        )

        temp_a4 = k_fc * max_nm * (fus_length ** 0.66 + b_50 ** 0.66)

        outputs["data:weight:airframe:flight_controls:mass"] = k_a4 * temp_a4 + offset_a4
