"""
    Estimation of global center of gravity
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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
from fastoad.modules.geometry.cg_components.compute_cg_ratio_aft import ComputeCGratioAft
from fastoad.modules.geometry.cg_components.compute_cg_loadcase1 import ComputeCGLoadCase1
from fastoad.modules.geometry.cg_components.compute_cg_loadcase2 import ComputeCGLoadCase2
from fastoad.modules.geometry.cg_components.compute_cg_loadcase3 import ComputeCGLoadCase3
from fastoad.modules.geometry.cg_components.compute_cg_loadcase4 import ComputeCGLoadCase4
from fastoad.modules.geometry.cg_components.compute_max_cg_ratio import ComputeMaxCGratio

from openmdao.api import Group

class ComputeGlobalCG(Group):
    # TODO: Document equations. Cite sources
    """ Global center of gravity estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')
    
    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_subsystem('cg_ratio_aft', ComputeCGratioAft(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('cg_ratio_lc1', ComputeCGLoadCase1(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('cg_ratio_lc2', ComputeCGLoadCase2(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('cg_ratio_lc3', ComputeCGLoadCase3(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('cg_ratio_lc4', ComputeCGLoadCase4(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('cg_ratio_max', ComputeMaxCGratio(deriv_method=deriv_method), promotes=['*'])