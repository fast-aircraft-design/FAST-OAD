"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeCnBeta(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:fuselage_width_max', val=4.)
        self.add_input('geometry:fuselage_height_max', val=4.)
        self.add_input('geometry:fuselage_length', val=37.)
        self.add_input('geometry:fuselage_LAV', val=6.)
        self.add_input('geometry:fuselage_LAR', val=14.)
        self.add_input('tlar:cruise_Mach', val=0.78)
        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:wing_span', val=32.)
    
        self.add_output('dcn_beta', val=1.)
        
        self.declare_partials('dcn_beta', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        fus_length = inputs['geometry:fuselage_length']
        lav = inputs['geometry:fuselage_LAV']
        lar = inputs['geometry:fuselage_LAR']
        width_max = inputs['geometry:fuselage_width_max']
        height_max = inputs['geometry:fuselage_height_max']
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        cruise_Mach = inputs['tlar:cruise_Mach']
    
        l_f = math.sqrt(width_max * height_max)
        l_cyc = fus_length - lav - lar
        # estimation of fuselage volume
        volume_fus = math.pi * l_f**2 / 4 * (0.7 * lav + 0.5 * lar + l_cyc)
        # equation from raymer book eqn. 16.47
        cn_beta_fus = -1.3 * volume_fus / \
            wing_area / span * (l_f / width_max)
        cn_beta_goal = 0.0569 - 0.01694 * cruise_Mach + 0.15904 * cruise_Mach**2
        
        outputs['dcn_beta'] = cn_beta_goal - cn_beta_fus 