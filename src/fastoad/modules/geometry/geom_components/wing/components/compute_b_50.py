"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeB50(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_x4', val=18.)
        self.add_input('geometry:wing_y2', val=2.)
        self.add_input('geometry:wing_y4', val=16.)
        self.add_input('geometry:wing_l1', val=6.)
        self.add_input('geometry:wing_l4', val=1.5)
        self.add_input('geometry:wing_span', val=32.)
        
        self.add_output('geometry:wing_b_50', val=34.)
        
        self.declare_partials('geometry:wing_b_50', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        x4_wing = inputs['geometry:wing_x4']
        y2_wing = inputs['geometry:wing_y2']
        y4_wing = inputs['geometry:wing_y4']
        l1_wing = inputs['geometry:wing_l1']
        l4_wing = inputs['geometry:wing_l4']
        span = inputs['geometry:wing_span']
            
        sweep_50 = math.atan(
            (x4_wing + l4_wing * 0.5 - 0.5 * l1_wing) / (y4_wing - y2_wing))
        b_50 = span / math.cos(sweep_50)
    
        outputs['geometry:wing_b_50'] = b_50
        
