"""
    Estimation of global center of gravity
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

import openmdao.api as om

from fastoad.module_management.service_registry import RegisterSubmodel
from .compute_max_cg_ratio import ComputeMaxCGratio
from ..constants import SERVICE_EMPTY_AIRCRAFT_CG, SERVICE_GLOBAL_CG, SERVICE_LOAD_CASES_CG


@RegisterSubmodel(SERVICE_GLOBAL_CG, "fastoad.submodel.weight.cg.global.legacy")
class ComputeGlobalCG(om.Group):
    # TODO: Document equations. Cite sources
    """Global center of gravity estimation"""

    def setup(self):
        self.add_subsystem(
            "cg_ratio_empty",
            RegisterSubmodel.get_submodel(SERVICE_EMPTY_AIRCRAFT_CG),
            promotes=["*"],
        )
        self.add_subsystem(
            "cg_ratio_load_cases",
            RegisterSubmodel.get_submodel(SERVICE_LOAD_CASES_CG),
            promotes=["*"],
        )
        self.add_subsystem("cg_ratio_max", ComputeMaxCGratio(), promotes=["*"])
