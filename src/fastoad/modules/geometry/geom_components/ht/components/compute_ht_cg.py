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

        self.add_input('geometry:horizontal_tail:root_chord', val=np.nan, units='m')
        self.add_input('geometry:horizontal_tail:tip_chord', val=np.nan, units='m')
        self.add_input('geometry:horizontal_tail:distance_from_wing', val=np.nan, units='m')
        self.add_input('geometry:horizontal_tail:span', val=np.nan, units='m')
        self.add_input('geometry:wing:location', val=np.nan, units='m')
        self.add_input('geometry:horizontal_tail:sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:horizontal_tail:length', val=np.nan, units='m')
        self.add_input('geometry:ht_x0', val=np.nan, units='m')

        self.add_output('weight:airframe:tail_plane:horizontal:CG:x', units='m')

        self.declare_partials('weight:airframe:tail_plane:horizontal:CG:x', '*', method='fd')

    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:horizontal_tail:root_chord']
        tip_chord = inputs['geometry:horizontal_tail:tip_chord']
        b_h = inputs['geometry:horizontal_tail:span']
        sweep_25_ht = inputs['geometry:horizontal_tail:sweep_25']
        fa_length = inputs['geometry:wing:location']
        lp_ht = inputs['geometry:horizontal_tail:distance_from_wing']
        mac_ht = inputs['geometry:horizontal_tail:length']
        x0_ht = inputs['geometry:ht_x0']

        tmp = (root_chord * 0.25 + b_h / 2 *
                 math.tan(sweep_25_ht / 180. * math.pi) - tip_chord * 0.25)

        l_cg = 0.62 * (root_chord - tip_chord) + tip_chord
        x_cg_ht = 0.42 * l_cg + 0.38 * tmp
        x_cg_ht_absolute = lp_ht + fa_length - \
            0.25 * mac_ht + (x_cg_ht - x0_ht)

        outputs['weight:airframe:tail_plane:horizontal:CG:x'] = x_cg_ht_absolute
