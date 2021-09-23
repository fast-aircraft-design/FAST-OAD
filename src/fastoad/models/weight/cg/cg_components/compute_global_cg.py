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

from fastoad.models.weight.cg.cg_components import ComputeCGLoadCase1
from fastoad.models.weight.cg.cg_components.compute_cg_loadcase2 import ComputeCGLoadCase2
from fastoad.models.weight.cg.cg_components.compute_cg_loadcase3 import ComputeCGLoadCase3
from fastoad.models.weight.cg.cg_components.compute_cg_loadcase4 import ComputeCGLoadCase4
from fastoad.models.weight.cg.cg_components.compute_cg_ratio_aft import ComputeCGRatioAft
from fastoad.models.weight.cg.cg_components.compute_max_cg_ratio import ComputeMaxCGratio


class ComputeGlobalCG(om.Group):
    # TODO: Document equations. Cite sources
    """ Global center of gravity estimation """

    def setup(self):
        self.add_subsystem("cg_ratio_aft", ComputeCGRatioAft(), promotes=["*"])
        self.add_subsystem("cg_ratio_lc1", ComputeCGLoadCase1(), promotes_inputs=["*"])
        self.add_subsystem("cg_ratio_lc2", ComputeCGLoadCase2(), promotes_inputs=["*"])
        self.add_subsystem("cg_ratio_lc3", ComputeCGLoadCase3(), promotes_inputs=["*"])
        self.add_subsystem("cg_ratio_lc4", ComputeCGLoadCase4(), promotes_inputs=["*"])
        cg_ratio_aggregator = self.add_subsystem("cg_ratio_aggregator", om.MuxComp(vec_size=4))
        self.add_subsystem("cg_ratio_max", ComputeMaxCGratio(), promotes=["*"])

        # This part aggregates all CG ratios values in one vector variable.
        cg_ratio_aggregator.add_var("cg_ratios", shape=(1,), axis=0)
        for i in range(4):
            self.connect(
                f"cg_ratio_lc{i+1}.data:weight:aircraft:load_case_{i+1}:CG:MAC_position",
                f"cg_ratio_aggregator.cg_ratios_{i}",
            )
        self.connect(
            "cg_ratio_aggregator.cg_ratios", "data:weight:aircraft:load_cases:CG:MAC_position"
        )
