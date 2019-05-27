"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeHTMAC(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:ht_root_chord', val=4.5)
        self.add_input('geometry:ht_tip_chord', val=1.5)
        self.add_input('geometry:ht_sweep_25', val=28.)
        self.add_input('geometry:ht_span', val=12.)
        
        self.add_output('geometry:ht_length', val=3.5)
        self.add_output('geometry:ht_x0', val=35.)
        self.add_output('geometry:ht_y0', val=2.5)
        
        self.declare_partials('geometry:ht_length', ['geometry:ht_root_chord', 'geometry:ht_tip_chord'], method=deriv_method)
        self.declare_partials('geometry:ht_x0', ['geometry:ht_root_chord', 'geometry:ht_tip_chord',
                                                 'geometry:ht_sweep_25', 'geometry:ht_span'], method=deriv_method)
        self.declare_partials('geometry:ht_y0', ['geometry:ht_root_chord', 'geometry:ht_tip_chord',
                                                 'geometry:ht_span'], method=deriv_method)
        
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