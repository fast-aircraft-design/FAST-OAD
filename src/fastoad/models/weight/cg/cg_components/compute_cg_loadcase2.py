"""
    Estimation of center of gravity for load case 2
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

from fastoad.module_management.service_registry import RegisterSubmodel
from .compute_cg_loadcase import ComputeCGLoadCase


CASE_NUMBER = 2


@RegisterSubmodel(
    f"service.cg.load_case.{CASE_NUMBER}",
    f"fastoad.submodel.weight.cg.load_case.legacy.{CASE_NUMBER}",
)
class ComputeCGLoadCase2(ComputeCGLoadCase):
    """ Center of gravity estimation for load case 3 """

    def setup(self):
        self.options["case_number"] = CASE_NUMBER
        self.options["weight_per_pax"] = 90.0
        self.options["weight_front_fret_per_pax"] = 20.0
        self.options["weight_rear_fret_per_pax"] = 20.0
        self.options["weight_fuel_variable"] = "data:weight:aircraft:MFW"
        return super().setup()
