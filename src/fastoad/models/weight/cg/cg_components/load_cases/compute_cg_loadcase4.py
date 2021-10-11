"""
    Estimation of center of gravity for load case 4
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
from .compute_cg_loadcase_base import ComputeCGLoadCase
from .compute_cg_loadcases import SERVICE_LOAD_CASE_CG_PREFIX

CASE_NUMBER = 4


@RegisterSubmodel(
    f"{SERVICE_LOAD_CASE_CG_PREFIX}.{CASE_NUMBER}",
    f"fastoad.submodel.weight.cg.load_case.legacy.{CASE_NUMBER}",
)
class ComputeCGLoadCase4(ComputeCGLoadCase):
    """Center of gravity estimation for load case"""

    def setup(self):
        self.options["case_number"] = CASE_NUMBER
        self.options["mass_per_pax"] = 90.0
        self.options["mass_front_fret_per_pax"] = 10.0
        self.options["mass_rear_fret_per_pax"] = 30.0
        return super().setup()
