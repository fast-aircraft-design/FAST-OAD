"""
    Estimation of vertical tail mean aerodynamic chords
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
class ComputeVTMAC(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail mean aerodynamic chord estimation """

    def setup(self):

        self.add_input('geometry:vt_root_chord', val=np.nan, units='m')
        self.add_input('geometry:vt_tip_chord', val=np.nan, units='m')
        self.add_input('geometry:vt_sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:vt_span', val=np.nan, units='m')

        self.add_output('geometry:vt_length', units='m')
        self.add_output('geometry:vt_x0', units='m')
        self.add_output('geometry:vt_z0', units='m')

        self.declare_partials('geometry:vt_length',
                              ['geometry:vt_root_chord', 'geometry:vt_tip_chord'])
        self.declare_partials('geometry:vt_x0', '*', method='fd')
        self.declare_partials('geometry:vt_z0',
                              ['geometry:vt_root_chord', 'geometry:vt_tip_chord',
                               'geometry:vt_span'], method='fd')

    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:vt_root_chord']
        tip_chord = inputs['geometry:vt_tip_chord']
        sweep_25_vt = inputs['geometry:vt_sweep_25']
        b_v = inputs['geometry:vt_span']

        tmp = (root_chord * 0.25 + b_v * math.tan(sweep_25_vt / 180. * math.pi) - tip_chord * 0.25)

        mac_vt = (root_chord ** 2 + root_chord * tip_chord + tip_chord ** 2) / \
                 (tip_chord + root_chord) * 2. / 3.
        x0_vt = (tmp * (root_chord + 2 * tip_chord)) / \
                (3 * (root_chord + tip_chord))
        z0_vt = (2 * b_v * (0.5 * root_chord + tip_chord)) / \
                (3 * (root_chord + tip_chord))

        outputs['geometry:vt_length'] = mac_vt
        outputs['geometry:vt_x0'] = x0_vt
        outputs['geometry:vt_z0'] = z0_vt
