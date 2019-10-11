"""
    Estimation of horizontal tail center of gravity
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


class ComputeHTcg(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail center of gravity estimation """

    def setup(self):

        self.add_input('geometry:ht_root_chord', val=np.nan, units='m')
        self.add_input('geometry:ht_tip_chord', val=np.nan, units='m')
        self.add_input('geometry:ht_lp', val=np.nan, units='m')
        self.add_input('geometry:ht_span', val=np.nan, units='m')
        self.add_input('geometry:wing_position', val=np.nan, units='m')
        self.add_input('geometry:ht_sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:ht_length', val=np.nan, units='m')
        self.add_input('geometry:ht_x0', val=np.nan, units='m')

        self.add_output('cg_airframe:A31', units='m')

        self.declare_partials('cg_airframe:A31', '*', method='fd')

    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:ht_root_chord']
        tip_chord = inputs['geometry:ht_tip_chord']
        b_h = inputs['geometry:ht_span']
        sweep_25_ht = inputs['geometry:ht_sweep_25']
        fa_length = inputs['geometry:wing_position']
        lp_ht = inputs['geometry:ht_lp']
        mac_ht = inputs['geometry:ht_length']
        x0_ht = inputs['geometry:ht_x0']

        tmp = (root_chord * 0.25 + b_h / 2 *
                 math.tan(sweep_25_ht / 180. * math.pi) - tip_chord * 0.25)

        l_cg = 0.62 * (root_chord - tip_chord) + tip_chord
        x_cg_ht = 0.42 * l_cg + 0.38 * tmp
        x_cg_ht_absolute = lp_ht + fa_length - \
            0.25 * mac_ht + (x_cg_ht - x0_ht)

        outputs['cg_airframe:A31'] = x_cg_ht_absolute
