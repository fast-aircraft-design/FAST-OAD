"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeMFW(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:wing_aspect_ratio', val=9.48)
        self.add_input('geometry:wing_toc_root', val=0.128)
        self.add_input('geometry:wing_toc_tip', val=0.128)
        
        self.add_output('weight:MFW', val=20000.)
        
        self.declare_partials('weight:MFW', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        lambda_wing = inputs['geometry:wing_aspect_ratio']
        el_emp = inputs['geometry:wing_toc_root']
        el_ext = inputs['geometry:wing_toc_tip']
        
        mfw = 224 * (wing_area ** 1.5 * lambda_wing ** (-0.4)
                     * (0.6 * el_emp + 0.4 * el_ext)) + 1570

        outputs['weight:MFW'] = mfw   
        