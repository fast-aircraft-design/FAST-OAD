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

import numpy as np
import openmdao.api as om

from fastoad.module_management.exceptions import FastNoSubmodelFoundError
from fastoad.module_management.service_registry import RegisterSubmodel
from .compute_cg_ratio_aft import ComputeCGRatioAft
from .compute_max_cg_ratio import ComputeMaxCGratio
from ..constants import SERVICE_GLOBAL_CG


@RegisterSubmodel(SERVICE_GLOBAL_CG, "fastoad.submodel.weight.cg.global.legacy")
class ComputeGlobalCG(om.Group):
    # TODO: Document equations. Cite sources
    """ Global center of gravity estimation """

    def setup(self):
        self.add_subsystem("cg_ratio_aft", ComputeCGRatioAft(), promotes=["*"])
        self.add_subsystem("cg_ratio_load_cases", CGRatiosForLoadCases(), promotes=["*"])
        self.add_subsystem("cg_ratio_max", ComputeMaxCGratio(), promotes=["*"])


class CGRatiosForLoadCases(om.Group):
    """Aggregation of CG ratios from load case calculations."""

    def setup(self):

        # We add in our group all the components for declared services that provide CG ratio
        # for specific load_cases
        load_case_count = 0
        found = True
        while found:
            try:
                system = RegisterSubmodel.get_submodel(
                    f"service.cg.load_case.{load_case_count + 1}"
                )
            except FastNoSubmodelFoundError:
                found = False
                continue
            self.add_subsystem(f"cg_ratio_lc{load_case_count + 1}", system, promotes_inputs=["*"])
            load_case_count += 1

        cg_ratio_aggregator = self.add_subsystem(
            "cg_ratio_aggregator",
            om.MuxComp(vec_size=load_case_count),
            promotes=["data:weight:aircraft:load_cases:CG:MAC_position"],
        )

        # This part aggregates all CG ratios values in one vector variable.
        cg_ratio_aggregator.add_var(
            "data:weight:aircraft:load_cases:CG:MAC_position", shape=(1,), axis=0
        )
        for i in range(load_case_count):
            self.connect(
                f"cg_ratio_lc{i + 1}.data:weight:aircraft:load_case_{i + 1}:CG:MAC_position",
                f"cg_ratio_aggregator.data:weight:aircraft:load_cases:CG:MAC_position_{i}",
            )

        self.add_subsystem("compute_max", MaxCGRatiosForLoadCases(), promotes=["*"])


class MaxCGRatiosForLoadCases(om.ExplicitComponent):
    """Maximum center of gravity ratio from load cases."""

    def setup(self):
        self.add_input(
            "data:weight:aircraft:load_cases:CG:MAC_position", val=np.nan, shape_by_conn=True
        )

        self.add_output("data:weight:aircraft:load_cases:CG:MAC_position:maximum")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        outputs["data:weight:aircraft:load_cases:CG:MAC_position:maximum"] = (
            np.nanmax(inputs["data:weight:aircraft:load_cases:CG:MAC_position"]),
        )
