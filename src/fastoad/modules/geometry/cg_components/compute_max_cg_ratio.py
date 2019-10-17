"""
    Estimation of maximum center of gravity ratio
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
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeMaxCGratio(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Maximum center of gravity ratio estimation """

    def setup(self):

        self.add_input('cg_ratio_aft', val=np.nan)

        for i in range(4):
            self.add_input('cg_ratio_lc'+str(i+1), val=np.nan)

        self.add_output('cg_ratio')

        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        outputs['cg_ratio'] = max(inputs['cg_ratio_aft'], inputs['cg_ratio_lc1'],
               inputs['cg_ratio_lc2'], inputs['cg_ratio_lc3'], inputs['cg_ratio_lc4'])
