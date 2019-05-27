"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeSweepWing(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_x3', val=16.)
        self.add_input('geometry:wing_x4', val=18.)
        self.add_input('geometry:wing_y2', val=2.)
        self.add_input('geometry:wing_y3', val=6.)
        self.add_input('geometry:wing_y4', val=16.)
        self.add_input('geometry:wing_l2', val=6.)
        self.add_input('geometry:wing_l3', val=4.)
        self.add_input('geometry:wing_l4', val=1.5)
        
        self.add_output('geometry:wing_sweep_0', val=27.)
        self.add_output('geometry:wing_sweep_100_inner', val=0.)
        self.add_output('geometry:wing_sweep_100_outer', val=33.)
        
        self.declare_partials('geometry:wing_sweep_0', ['geometry:wing_x3', 'geometry:wing_y2',
                                                        'geometry:wing_y3'], method=deriv_method)
        self.declare_partials('geometry:wing_sweep_100_inner', ['geometry:wing_x3', 'geometry:wing_l2',
                                                                'geometry:wing_y2', 'geometry:wing_y3',
                                                                'geometry:wing_l3'], method=deriv_method)
        self.declare_partials('geometry:wing_sweep_100_outer', ['geometry:wing_x3', 'geometry:wing_x4',
                                                                'geometry:wing_y3', 'geometry:wing_y4', 
                                                                'geometry:wing_l3', 'geometry:wing_l4'], method=deriv_method)
        
    def compute(self, inputs, outputs):
        x3_wing = inputs['geometry:wing_x3']
        x4_wing = inputs['geometry:wing_x4']
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        l2_wing = inputs['geometry:wing_l2']
        l3_wing = inputs['geometry:wing_l3']
        l4_wing = inputs['geometry:wing_l4']
        
        outputs['geometry:wing_sweep_0'] = math.atan(x3_wing / (y3_wing - y2_wing)) / math.pi * 180.
        outputs['geometry:wing_sweep_100_inner'] = math.atan(
            (x3_wing + l3_wing - l2_wing) / (y3_wing - y2_wing)) / math.pi * 180
        outputs['geometry:wing_sweep_100_outer'] = math.atan(
            (x4_wing + l4_wing - x3_wing - l3_wing) / (y4_wing - y3_wing)) / math.pi * 180.
                