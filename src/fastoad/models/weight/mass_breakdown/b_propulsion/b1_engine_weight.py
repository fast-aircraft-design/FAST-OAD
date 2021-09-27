"""
Estimation of engine weight
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
from .constants import SERVICE_ENGINE_MASS


# TODO:  this is also provided by class RubberEngine
@RegisterSubmodel(SERVICE_ENGINE_MASS, "fastoad.submodel.weight.mass.propulsion.engine.legacy")
class EngineWeight(om.ExplicitComponent):
    """
    Engine weight estimation

    Uses model described in :cite:`roux:2005`, p.74
    """

    def setup(self):
        self.add_input("data:propulsion:MTO_thrust", val=np.nan, units="N")
        self.add_input("data:geometry:propulsion:engine:count", val=np.nan)
        self.add_input("tuning:weight:propulsion:engine:mass:k", val=1.0)
        self.add_input("tuning:weight:propulsion:engine:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:propulsion:engine:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        sea_level_thrust = inputs["data:propulsion:MTO_thrust"]
        n_engines = inputs["data:geometry:propulsion:engine:count"]
        k_b1 = inputs["tuning:weight:propulsion:engine:mass:k"]
        offset_b1 = inputs["tuning:weight:propulsion:engine:mass:offset"]

        if sea_level_thrust < 80000:
            temp_b1 = 22.2e-3 * sea_level_thrust
        else:
            temp_b1 = 14.1e-3 * sea_level_thrust + 648

        temp_b1 *= n_engines * 1.55
        outputs["data:weight:propulsion:engine:mass"] = k_b1 * temp_b1 + offset_b1
