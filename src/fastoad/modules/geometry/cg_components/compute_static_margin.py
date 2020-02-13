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
        self.add_input('weight:aircraft:CG:ratio', val=np.nan)
        self.add_input('aerodynamics:cruise:neutral_point:x', val=np.nan)
        self.add_input('geometry:wing:MAC:x', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:length', val=np.nan, units='m')

        self.add_output('handling_qualities:static_margin')
        self.add_output('weight:aircraft:CG:x', units='m')

        self.declare_partials('handling_qualities:static_margin',
                              ['weight:aircraft:CG:ratio', 'aerodynamics:cruise:neutral_point:x'],
                              method='fd')
        self.declare_partials('weight:aircraft:CG:x',
                              ['geometry:wing:MAC:x', 'weight:aircraft:CG:ratio',
                               'geometry:wing:MAC:length'],
                              method='fd')

    def compute(self, inputs, outputs):
        cg_ratio = inputs['weight:aircraft:CG:ratio'] + 0.05
        ac_ratio = inputs['aerodynamics:cruise:neutral_point:x']
        l0_wing = inputs['geometry:wing:MAC:length']
        fa_length = inputs['geometry:wing:MAC:x']

        outputs['weight:aircraft:CG:x'] = fa_length - 0.25 * l0_wing + cg_ratio * l0_wing
        outputs['handling_qualities:static_margin'] = ac_ratio - cg_ratio
