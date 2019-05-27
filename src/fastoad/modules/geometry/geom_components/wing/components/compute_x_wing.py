"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeXWing(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_l1', val=6.)
        self.add_input('geometry:wing_l3', val=4.)
        self.add_input('geometry:wing_l4', val=1.5)
        self.add_input('geometry:wing_y2', val=2.)
        self.add_input('geometry:wing_y3', val=4.)
        self.add_input('geometry:wing_y4', val=16.)
        self.add_input('geometry:wing_sweep_25', val=25.)
        
        self.add_output('geometry:wing_x3', val=16.)
        self.add_output('geometry:wing_x4', val=18.)
        
        self.declare_partials('geometry:wing_x3', ['geometry:wing_l1', 'geometry:wing_y2',
                                                   'geometry:wing_y3', 'geometry:wing_l3',
                                                   'geometry:wing_sweep_25'], method=deriv_method)
        self.declare_partials('geometry:wing_x4', ['geometry:wing_l1', 'geometry:wing_y2',
                                                   'geometry:wing_y4', 'geometry:wing_l4',
                                                   'geometry:wing_sweep_25'], method=deriv_method)
        
    def compute(self, inputs, outputs):
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        l1_wing = inputs['geometry:wing_l1']
        l3_wing = inputs['geometry:wing_l3']
        l4_wing = inputs['geometry:wing_l4']
        sweep_25 = inputs['geometry:wing_sweep_25']
    
        x3_wing = 1. / 4. * l1_wing + \
            (y3_wing - y2_wing) * \
            math.tan(sweep_25 / 180. * math.pi) - 1. / 4. * l3_wing
        x4_wing = 1. / 4. * l1_wing + \
            (y4_wing - y2_wing) * \
            math.tan(sweep_25 / 180. * math.pi) - 1. / 4. * l4_wing
            
        outputs['geometry:wing_x3'] = x3_wing
        outputs['geometry:wing_x4'] = x4_wing
        
 