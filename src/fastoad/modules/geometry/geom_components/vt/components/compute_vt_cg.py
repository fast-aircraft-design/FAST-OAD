"""
    Estimation of vertical tail center of gravity
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
import math

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeVTcg(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail center of gravity estimation """

    def setup(self):

        self.add_input('geometry:vertical_tail:length', val=np.nan, units='m')
        self.add_input('geometry:vertical_tail:root_chord', val=np.nan, units='m')
        self.add_input('geometry:vertical_tail:tip_chord', val=np.nan, units='m')
        self.add_input('geometry:vertical_tail:distance_from_wing', val=np.nan, units='m')
        self.add_input('geometry:vt_x0', val=np.nan, units='m')
        self.add_input('geometry:vertical_tail:sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:vertical_tail:span', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:x', val=np.nan, units='m')

        self.add_output('weight:airframe:vertical_tail:CG:x', units='m')

        self.declare_partials('weight:airframe:vertical_tail:CG:x', '*', method='fd')

    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:vertical_tail:root_chord']
        tip_chord = inputs['geometry:vertical_tail:tip_chord']
        lp_vt = inputs['geometry:vertical_tail:distance_from_wing']
        mac_vt = inputs['geometry:vertical_tail:length']
        fa_length = inputs['geometry:wing:MAC:x']
        x0_vt = inputs['geometry:vt_x0']
        sweep_25_vt = inputs['geometry:vertical_tail:sweep_25']
        b_v = inputs['geometry:vertical_tail:span']

        tmp = root_chord * 0.25 + b_v * math.tan(sweep_25_vt / 180. * math.pi) - tip_chord * 0.25
        l_cg_vt = (1 - 0.55) * (root_chord - tip_chord) + tip_chord
        x_cg_vt = 0.42 * l_cg_vt + 0.55 * tmp
        x_cg_vt_absolute = lp_vt + fa_length - \
                           0.25 * mac_vt + (x_cg_vt - x0_vt)

        outputs['weight:airframe:vertical_tail:CG:x'] = x_cg_vt_absolute
