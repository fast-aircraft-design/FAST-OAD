"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeVTChords(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:vt_aspect_ratio', val=1.5)
        self.add_input('geometry:vt_area', val=45.)
        self.add_input('geometry:vt_taper_ratio', val=0.3)

        self.add_output('geometry:vt_span', val=10.)
        self.add_output('geometry:vt_root_chord', val=6.)
        self.add_output('geometry:vt_tip_chord', val=2.)
        
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