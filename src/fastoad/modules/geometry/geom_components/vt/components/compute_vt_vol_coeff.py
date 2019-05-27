"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeVTVolCoeff(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:vt_area', val=45.)
        self.add_input('geometry:vt_lp', val=18.)
        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:wing_span', val=32.)
        
        self.add_output('geometry:vt_vol_coeff', val=0.1)
        
        self.declare_partials('geometry:vt_vol_coeff', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        outputs['geometry:vt_vol_coeff'] = inputs['geometry:vt_area'] * inputs['geometry:vt_lp'] / \
            (inputs['geometry:wing_area'] * inputs['geometry:wing_span'])