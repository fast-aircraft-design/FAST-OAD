"""
    Estimation of static margin
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

class ComputeStaticMargin(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Static margin estimation """

    def setup(self):

        self.add_input('cg_ratio', val=np.nan)
        self.add_input('x_ac_ratio', val=np.nan)
        self.add_input('geometry:wing_position', val=np.nan, units='m')
        self.add_input('geometry:wing_l0', val=np.nan, units='m')

        self.add_output('static_margin')
        self.add_output('cg:CG', units='m')

        self.declare_partials('static_margin', ['cg_ratio', 'x_ac_ratio'], method='fd')
        self.declare_partials('cg:CG',
                              ['geometry:wing_position', 'cg_ratio', 'geometry:wing_l0'],
                              method='fd')

    def compute(self, inputs, outputs):
        cg_ratio = inputs['cg_ratio']
        cg_ratio += 0.05
        ac_ratio = inputs['x_ac_ratio']
        l0_wing = inputs['geometry:wing_l0']
        fa_length = inputs['geometry:wing_position']

        outputs['cg:CG'] = fa_length - 0.25 * l0_wing + cg_ratio * l0_wing
        outputs['static_margin'] = ac_ratio - cg_ratio
