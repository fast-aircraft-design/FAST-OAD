"""
    Estimation of horizontal tail mean aerodynamic chords
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
import math

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


# TODO: it would be good to have a function to compute MAC for HT, VT and WING
class ComputeHTMAC(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail mean aerodynamic chord estimation """

    def setup(self):

        self.add_input('geometry:horizontal_tail:root_chord', val=np.nan, units='m')
        self.add_input('geometry:horizontal_tail:tip_chord', val=np.nan, units='m')
        self.add_input('geometry:horizontal_tail:sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:horizontal_tail:span', val=np.nan, units='m')

        self.add_output('geometry:horizontal_tail:MAC:length', units='m')
        self.add_output('geometry:horizontal_tail:MAC:x', units='m')
        self.add_output('geometry:horizontal_tail:MAC:y', units='m')

        self.declare_partials('geometry:horizontal_tail:MAC:length',
                              ['geometry:horizontal_tail:root_chord',
                               'geometry:horizontal_tail:tip_chord'],
                              method='fd')
        self.declare_partials('geometry:horizontal_tail:MAC:x',
                              ['geometry:horizontal_tail:root_chord',
                               'geometry:horizontal_tail:tip_chord',
                               'geometry:horizontal_tail:sweep_25',
                               'geometry:horizontal_tail:span'],
                              method='fd')
        self.declare_partials('geometry:horizontal_tail:MAC:y',
                              ['geometry:horizontal_tail:root_chord',
                               'geometry:horizontal_tail:tip_chord',
                               'geometry:horizontal_tail:span'], method='fd')

    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:horizontal_tail:root_chord']
        tip_chord = inputs['geometry:horizontal_tail:tip_chord']
        sweep_25_ht = inputs['geometry:horizontal_tail:sweep_25']
        b_h = inputs['geometry:horizontal_tail:span']

        tmp = (root_chord * 0.25 + b_h / 2 *
               math.tan(sweep_25_ht / 180. * math.pi) - tip_chord * 0.25)

        mac_ht = (root_chord ** 2 + root_chord * tip_chord + tip_chord ** 2) / \
                 (tip_chord + root_chord) * 2 / 3
        x0_ht = (tmp * (root_chord + 2 * tip_chord)) / \
                (3 * (root_chord + tip_chord))
        y0_ht = (b_h * (.5 * root_chord + tip_chord)) / \
                (3 * (root_chord + tip_chord))

        outputs['geometry:horizontal_tail:MAC:length'] = mac_ht
        outputs['geometry:horizontal_tail:MAC:x'] = x0_ht
        outputs['geometry:horizontal_tail:MAC:y'] = y0_ht
