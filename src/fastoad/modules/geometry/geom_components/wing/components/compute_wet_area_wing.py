"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeWetAreaWing(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_l2', val=6.)
        self.add_input('geometry:wing_y2', val=2.)
        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:fuselage_width_max', val=4.)
        
        self.add_output('geometry:wing_area_pf', val=50.)
        self.add_output('geometry:wing_wet_area', val=200.)
        
        self.declare_partials('geometry:wing_area_pf', ['geometry:wing_area', 'geometry:wing_y2',
                                                        'geometry:wing_l2'], method=deriv_method)
        self.declare_partials('geometry:wing_wet_area', ['geometry:wing_area', 'geometry:wing_l2',
                                                         'geometry:fuselage_width_max'], method=deriv_method)
        
    def compute(self, inputs, outputs):
         wing_area = inputs['geometry:wing_area']
         l2_wing = inputs['geometry:wing_l2']
         y2_wing = inputs['geometry:wing_y2']
         width_max = inputs['geometry:fuselage_width_max']
         
         s_pf = wing_area - 2 * l2_wing * y2_wing 
         wet_area_wing = 2 * (wing_area - width_max * l2_wing)
         
         outputs['geometry:wing_area_pf'] = s_pf
         outputs['geometry:wing_wet_area'] = wet_area_wing