"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""
import math 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeL2AndL3Wing(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_span', val=32.)
        self.add_input('geometry:wing_sweep_25', val=25.)
        self.add_input('geometry:wing_l1', val=6.)
        self.add_input('geometry:wing_l4', val=1.5)
        self.add_input('geometry:wing_y2', val=2.)
        self.add_input('geometry:wing_y3', val=4.)
        self.add_input('geometry:wing_y4', val=16.)
        self.add_input('geometry:wing_taper_ratio', val=0.38)
        self.add_input('geometry:fuselage_width_max', val=4.)
        
        self.add_output('geometry:wing_l2', val=6.)
        self.add_output('geometry:wing_l3', val=4.)
        
        self.declare_partials('geometry:wing_l2', ['geometry:wing_l1', 'geometry:wing_y2',
                                                   'geometry:wing_y3', 'geometry:wing_taper_ratio', 
                                                   'geometry:wing_span', 'geometry:fuselage_width_max',
                                                   'geometry:wing_sweep_25'], method=deriv_method)
        self.declare_partials('geometry:wing_l3', ['geometry:wing_l1', 'geometry:wing_l4', 'geometry:wing_y2',
                                                   'geometry:wing_y3', 'geometry:wing_y4'], method=deriv_method)
        
    def compute(self, inputs, outputs):
        l1_wing = inputs['geometry:wing_l1']
        l4_wing = inputs['geometry:wing_l4']
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        span = inputs['geometry:wing_span']
        width_max = inputs['geometry:fuselage_width_max']
        taper_ratio = inputs['geometry:wing_taper_ratio']
        sweep_25 = inputs['geometry:wing_sweep_25']
        
        l2_wing = (l1_wing +
                   (y3_wing -
                    y2_wing) *
                   (math.tan(sweep_25 / 180. * math.pi) -
                    3. / 2. * (1. - taper_ratio) / (span - width_max) * l1_wing))

        l3_wing = l4_wing + (l1_wing - l4_wing) * \
            (y4_wing - y3_wing) / (y4_wing - y2_wing)
            
        outputs['geometry:wing_l2'] = l2_wing
        outputs['geometry:wing_l3'] = l3_wing
        
