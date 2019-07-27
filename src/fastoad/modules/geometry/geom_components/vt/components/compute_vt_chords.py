"""
    Estimation of vertical tail chords and span
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

class ComputeVTChords(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail chords and span estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:vt_aspect_ratio', val=np.nan)
        self.add_input('geometry:vt_area', val=np.nan, units='m**2')
        self.add_input('geometry:vt_taper_ratio', val=np.nan)

        self.add_output('geometry:vt_span', units='m')
        self.add_output('geometry:vt_root_chord', units='m')
        self.add_output('geometry:vt_tip_chord', units='m')
        
        self.declare_partials('geometry:vt_span', ['geometry:vt_aspect_ratio', 'geometry:vt_area'], method=deriv_method)
        self.declare_partials('geometry:vt_root_chord', '*', method=deriv_method)
        self.declare_partials('geometry:vt_tip_chord', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        lambda_vt = inputs['geometry:vt_aspect_ratio']
        s_v = inputs['geometry:vt_area']
        taper_v = inputs['geometry:vt_taper_ratio']
        
        b_v = math.sqrt(lambda_vt * s_v)
        root_chord = s_v * 2 / (1 + taper_v) / b_v
        tip_chord = root_chord * taper_v

        outputs['geometry:vt_span'] = b_v
        outputs['geometry:vt_root_chord'] = root_chord
        outputs['geometry:vt_tip_chord'] = tip_chord