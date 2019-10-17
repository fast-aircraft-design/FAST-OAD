"""
    Estimation of horizontal tail mean aerodynamic chords
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


# TODO: it would be good to have a function to compute MAC for HT, VT and WING
class ComputeHTMAC(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail mean aerodynamic chord estimation """

    def setup(self):

        self.add_input('geometry:ht_root_chord', val=np.nan, units='m')
        self.add_input('geometry:ht_tip_chord', val=np.nan, units='m')
        self.add_input('geometry:ht_sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:ht_span', val=np.nan, units='m')

        self.add_output('geometry:ht_length', units='m')
        self.add_output('geometry:ht_x0', units='m')
        self.add_output('geometry:ht_y0', units='m')

        self.declare_partials('geometry:ht_length',
                              ['geometry:ht_root_chord', 'geometry:ht_tip_chord'],
                              method='fd')
        self.declare_partials('geometry:ht_x0',
                              ['geometry:ht_root_chord', 'geometry:ht_tip_chord',
                               'geometry:ht_sweep_25', 'geometry:ht_span'],
                              method='fd')
        self.declare_partials('geometry:ht_y0',
                              ['geometry:ht_root_chord', 'geometry:ht_tip_chord',
                               'geometry:ht_span'], method='fd')

    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:ht_root_chord']
        tip_chord = inputs['geometry:ht_tip_chord']
        sweep_25_ht = inputs['geometry:ht_sweep_25']
        b_h = inputs['geometry:ht_span']

        tmp = (root_chord * 0.25 + b_h / 2 *
               math.tan(sweep_25_ht / 180. * math.pi) - tip_chord * 0.25)

        mac_ht = (root_chord**2 + root_chord * tip_chord + tip_chord**2) / \
            (tip_chord + root_chord) * 2 / 3
        x0_ht = (tmp * (root_chord + 2 * tip_chord)) / \
            (3 * (root_chord + tip_chord))
        y0_ht = (b_h * (.5 * root_chord + tip_chord)) / \
            (3 * (root_chord + tip_chord))

        outputs['geometry:ht_length'] = mac_ht
        outputs['geometry:ht_x0'] = x0_ht
        outputs['geometry:ht_y0'] = y0_ht
