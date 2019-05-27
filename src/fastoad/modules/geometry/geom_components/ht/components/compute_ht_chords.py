"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeHTChord(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:ht_aspect_ratio', val=4.5)
        self.add_input('geometry:ht_area', val=70.)
        self.add_input('geometry:ht_taper_ratio', val=0.3)
        
        self.add_output('geometry:ht_span', val=12.)
        self.add_output('geometry:ht_root_chord', val=4.5)
        self.add_output('geometry:ht_tip_chord', val=1.5)
        
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