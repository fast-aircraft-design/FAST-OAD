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
        self.add_subsystem("cg_ratio_aggregator", self._cg_ratios_for_load_cases())
        self.add_subsystem("cg_ratio_max", ComputeMaxCGratio(), promotes=["*"])

    def _cg_ratios_for_load_cases(self) -> om.MuxComp:
        """
        Adds a component that aggregates all CG ratios computed for specific load cases.
        :return:
        """
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
        cg_ratio_aggregator = om.MuxComp(vec_size=load_case_count)

        # This part aggregates all CG ratios values in one vector variable.
        cg_ratio_aggregator.add_var("cg_ratios", shape=(1,), axis=0)
        for i in range(load_case_count):
            self.connect(
                f"cg_ratio_lc{i + 1}.data:weight:aircraft:load_case_{i + 1}:CG:MAC_position",
                f"cg_ratio_aggregator.cg_ratios_{i}",
            )
        self.connect(
            "cg_ratio_aggregator.cg_ratios", "data:weight:aircraft:load_cases:CG:MAC_position"
        )
        return cg_ratio_aggregator
