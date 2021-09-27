"""
Estimation of passenger seats weight
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
from .constants import SERVICE_PASSENGER_SEATS_MASS


@RegisterSubmodel(SERVICE_PASSENGER_SEATS_MASS, "service.mass.furniture.passenger_seats.legacy")
class PassengerSeatsWeight(om.ExplicitComponent):
    """
    Weight estimation for passenger seats

    Based on :cite:`supaero:2014`, mass contribution D2
    """

    def setup(self):
        self.add_input("data:TLAR:range", val=np.nan, units="NM")
        self.add_input("data:TLAR:NPAX", val=np.nan)
        self.add_input("tuning:weight:furniture:passenger_seats:mass:k", val=1.0)
        self.add_input("tuning:weight:furniture:passenger_seats:mass:offset", val=0.0, units="kg")

        self.add_output("data:weight:furniture:passenger_seats:mass", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        tlar_range = inputs["data:TLAR:range"]
        npax = inputs["data:TLAR:NPAX"]
        k_d2 = inputs["tuning:weight:furniture:passenger_seats:mass:k"]
        offset_d2 = inputs["tuning:weight:furniture:passenger_seats:mass:offset"]

        if tlar_range in RangeCategory.SHORT:
            k_ps = 9.0
        elif RangeCategory.SHORT_MEDIUM.min() <= tlar_range <= RangeCategory.MEDIUM.max():
            k_ps = 10.0
        else:
            k_ps = 11.0

        temp_d2 = k_ps * npax
        outputs["data:weight:furniture:passenger_seats:mass"] = k_d2 * temp_d2 + offset_d2
