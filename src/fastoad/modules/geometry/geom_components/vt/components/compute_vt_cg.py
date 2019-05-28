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
import numpy as np
import math 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeVTcg(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail center of gravity estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:vt_length', val=np.nan)
        self.add_input('geometry:vt_root_chord', val=np.nan)
        self.add_input('geometry:vt_tip_chord', val=np.nan)
        self.add_input('geometry:vt_lp', val=np.nan)
        self.add_input('geometry:vt_x0', val=np.nan)
        self.add_input('geometry:vt_sweep_25', val=np.nan)
        self.add_input('geometry:vt_span', val=np.nan)
        self.add_input('geometry:wing_position', val=np.nan)
        
        self.add_output('cg_airframe:A32')
        
        self.declare_partials('cg_airframe:A32', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:vt_root_chord']
        tip_chord = inputs['geometry:vt_tip_chord']
        lp_vt = inputs['geometry:vt_lp']
        mac_vt = inputs['geometry:vt_length']
        fa_length = inputs['geometry:wing_position']
        x0_vt = inputs['geometry:vt_x0']
        sweep_25_vt = inputs['geometry:vt_sweep_25']
        b_v = inputs['geometry:vt_span']
    
        tmp = root_chord * 0.25 + b_v * math.tan(sweep_25_vt / 180. * math.pi) - tip_chord * 0.25    
        l_cg_vt = (1 - 0.55) * (root_chord - tip_chord) + tip_chord
        x_cg_vt = 0.42 * l_cg_vt + 0.55 * tmp
        x_cg_vt_absolute = lp_vt + fa_length - \
            0.25 * mac_vt + (x_cg_vt - x0_vt)
            
        outputs['cg_airframe:A32'] = x_cg_vt_absolute