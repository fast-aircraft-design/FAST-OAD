"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeYwing(ExplicitComponent):
        
    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_aspect_ratio', val=9.48)
        self.add_input('geometry:fuselage_width_max', val=4.)
        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:wing_break', val=0.4)
        
        self.add_output('geometry:wing_span', val=32.)
        self.add_output('geometry:wing_y2', val=2.)
        self.add_output('geometry:wing_y3', val=4.)
        self.add_output('geometry:wing_y4', val=16.)
        
        self.declare_partials('geometry:wing_span', ['geometry:wing_area', 'geometry:wing_aspect_ratio'], method=deriv_method)
        self.declare_partials('geometry:wing_y2', 'geometry:fuselage_width_max', method=deriv_method)
        self.declare_partials('geometry:wing_y3', ['geometry:wing_area', 'geometry:wing_aspect_ratio',
                                                'geometry:wing_break'], method=deriv_method)
        self.declare_partials('geometry:wing_y4', ['geometry:wing_area', 'geometry:wing_aspect_ratio'], method=deriv_method)
        
    def compute(self, inputs, outputs):
        lambda_wing = inputs['geometry:wing_aspect_ratio']
        wing_area = inputs['geometry:wing_area']
        wing_break = inputs['geometry:wing_break']
        width_max = inputs['geometry:fuselage_width_max']

        span = math.sqrt(lambda_wing * wing_area)

        # Wing geometry
        y4_wing = span / 2.
        y2_wing = width_max / 2.
        y3_wing = y4_wing * wing_break
    
        outputs['geometry:wing_span'] = span
        outputs['geometry:wing_y2'] = y2_wing
        outputs['geometry:wing_y3'] = y3_wing
        outputs['geometry:wing_y4'] = y4_wing