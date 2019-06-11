"""
    Estimation of horizontal tail chords and span
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
import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeHTChord(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail chords and span estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:ht_aspect_ratio', val=np.nan)
        self.add_input('geometry:ht_area', val=np.nan)
        self.add_input('geometry:ht_taper_ratio', val=np.nan)
        
        self.add_output('geometry:ht_span')
        self.add_output('geometry:ht_root_chord')
        self.add_output('geometry:ht_tip_chord')
        
        self.declare_partials('geometry:ht_span', ['geometry:ht_area', 'geometry:ht_aspect_ratio'], method=deriv_method)
        self.declare_partials('geometry:ht_root_chord', '*', method=deriv_method)
        self.declare_partials('geometry:ht_tip_chord', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        lambda_ht = inputs['geometry:ht_aspect_ratio']
        s_h = inputs['geometry:ht_area']
        taper_ht = inputs['geometry:ht_taper_ratio']
        
        b_h = math.sqrt(lambda_ht * s_h)
        root_chord = s_h * 2 / (1 + taper_ht) / b_h
        tip_chord = root_chord * taper_ht

        outputs['geometry:ht_span'] = b_h
        outputs['geometry:ht_root_chord'] = root_chord
        outputs['geometry:ht_tip_chord'] = tip_chord