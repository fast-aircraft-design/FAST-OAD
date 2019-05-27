"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from openmdao.core.explicitcomponent import ExplicitComponent

class UpdateMLG(ExplicitComponent):
    
    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_l0', val=4.2)
        self.add_input('geometry:wing_position', val=0.)
        self.add_input('cg_ratio', val=0.)
        self.add_input('delta_lg', val=0.)

        self.add_output('cg_airframe:A51')
        
        self.declare_partials('cg_airframe:A51', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        l0_wing = inputs['geometry:wing_l0']
        fa_length = inputs['geometry:wing_position']
        cg_ratio = inputs['cg_ratio']
        delta_lg = inputs['delta_lg']
        
        x_cg = fa_length - 0.25 * l0_wing + cg_ratio * l0_wing
        
        cg_airframe_a51 = x_cg + 0.08 * delta_lg
        
        outputs['cg_airframe:A51'] = cg_airframe_a51
