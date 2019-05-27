"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeHTcg(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:ht_root_chord', val=4.5)
        self.add_input('geometry:ht_tip_chord', val=1.5)
        self.add_input('geometry:ht_lp', val=16.)
        self.add_input('geometry:ht_span', val=12.)
        self.add_input('geometry:wing_position', val=16.)
        self.add_input('geometry:ht_sweep_25', val=28.)
        self.add_input('geometry:ht_length', val=3.5)
        self.add_input('geometry:ht_x0', val=16.)
        
        self.add_output('cg_airframe:A31', val=30.)
        
        self.declare_partials('cg_airframe:A31', '*', method=deriv_method)
        
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