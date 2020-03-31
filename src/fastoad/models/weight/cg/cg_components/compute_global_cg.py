"""
    Estimation of global center of gravity
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

from fastoad.models.weight.cg.cg_components import ComputeCGLoadCase1
from fastoad.models.weight.cg.cg_components.compute_cg_loadcase2 import ComputeCGLoadCase2
from fastoad.models.weight.cg.cg_components.compute_cg_loadcase3 import ComputeCGLoadCase3
from fastoad.models.weight.cg.cg_components.compute_cg_loadcase4 import ComputeCGLoadCase4
from fastoad.models.weight.cg.cg_components.compute_cg_ratio_aft import ComputeCGRatioAft
from fastoad.models.weight.cg.cg_components.compute_max_cg_ratio import ComputeMaxCGratio

from openmdao.api import Group


class ComputeGlobalCG(Group):
    # TODO: Document equations. Cite sources
    """ Global center of gravity estimation """

    def setup(self):
        self.add_subsystem("cg_ratio_aft", ComputeCGRatioAft(), promotes=["*"])
        self.add_subsystem("cg_ratio_lc1", ComputeCGLoadCase1(), promotes=["*"])
        self.add_subsystem("cg_ratio_lc2", ComputeCGLoadCase2(), promotes=["*"])
        self.add_subsystem("cg_ratio_lc3", ComputeCGLoadCase3(), promotes=["*"])
        self.add_subsystem("cg_ratio_lc4", ComputeCGLoadCase4(), promotes=["*"])
        self.add_subsystem("cg_ratio_max", ComputeMaxCGratio(), promotes=["*"])
