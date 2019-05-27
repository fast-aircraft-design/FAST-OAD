"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeL1AndL4Wing(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:wing_y2', val=2.)
        self.add_input('geometry:wing_y3', val=4.)
        self.add_input('geometry:wing_span', val=32.)
        self.add_input('geometry:fuselage_width_max', val=4.)
        self.add_input('geometry:wing_taper_ratio', val=0.38)
        self.add_input('geometry:wing_sweep_25', val=25.)
        
        self.add_output('geometry:wing_l1', val=6.)
        self.add_output('geometry:wing_l4', val=1.5)
        
        self.declare_partials('geometry:wing_l1', '*', method=deriv_method)
        self.declare_partials('geometry:wing_l4', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        sweep_25 = inputs['geometry:wing_sweep_25']
        width_max = inputs['geometry:fuselage_width_max']
        taper_ratio = inputs['geometry:wing_taper_ratio']
        
        l1_wing = (wing_area - (y3_wing - y2_wing) * (y3_wing + y2_wing) *
                   math.tan(sweep_25 / 180. * math.pi)) / \
                   ((1. + taper_ratio) / 2. * (span - width_max) + width_max - \
                    (3. * (1. - taper_ratio) * (y3_wing - y2_wing) * (y3_wing + y2_wing))
                    / (2. * (span - width_max)))
        
        l4_wing = l1_wing * taper_ratio
        
        outputs['geometry:wing_l1'] = l1_wing
        outputs['geometry:wing_l4'] = l4_wing
        
