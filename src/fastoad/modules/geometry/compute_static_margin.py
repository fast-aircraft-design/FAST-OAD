"""
    Estimation of static margin
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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
        self.add_input('data:weight:aircraft:CG:ratio', val=np.nan)
        self.add_input('data:aerodynamics:cruise:neutral_point:x', val=np.nan)
        self.add_input('data:geometry:wing:MAC:x', val=np.nan, units='m')
        self.add_input('data:geometry:wing:MAC:length', val=np.nan, units='m')

        self.add_output('data:handling_qualities:static_margin')
        self.add_output('data:weight:aircraft:CG:x', units='m')

        self.declare_partials('data:handling_qualities:static_margin',
                              ['data:weight:aircraft:CG:ratio',
                               'data:aerodynamics:cruise:neutral_point:x'],
                              method='fd')
        self.declare_partials('data:weight:aircraft:CG:x',
                              ['data:geometry:wing:MAC:x', 'data:weight:aircraft:CG:ratio',
                               'data:geometry:wing:MAC:length'],
                              method='fd')

    def compute(self, inputs, outputs):
        cg_ratio = inputs['data:weight:aircraft:CG:ratio'] + 0.05
        ac_ratio = inputs['data:aerodynamics:cruise:neutral_point:x']
        l0_wing = inputs['data:geometry:wing:MAC:length']
        fa_length = inputs['data:geometry:wing:MAC:x']

        outputs['data:weight:aircraft:CG:x'] = fa_length - 0.25 * l0_wing + cg_ratio * l0_wing
        outputs['data:handling_qualities:static_margin'] = ac_ratio - cg_ratio
