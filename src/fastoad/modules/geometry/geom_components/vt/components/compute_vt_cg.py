"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeVTcg(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:vt_length', val=3.5)
        self.add_input('geometry:vt_root_chord', val=6.)
        self.add_input('geometry:vt_tip_chord', val=2.)
        self.add_input('geometry:vt_lp', val=20.)
        self.add_input('geometry:vt_x0', val=20.)
        self.add_input('geometry:vt_sweep_25', val=35.)
        self.add_input('geometry:vt_span', val=8.)
        self.add_input('geometry:wing_position', val=16.)
        
        self.add_output('cg_airframe:A32', val=35.)
        
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