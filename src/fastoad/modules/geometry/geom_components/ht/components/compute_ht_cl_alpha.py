"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeHTClalpha(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:ht_aspect_ratio', val=4.5)
        self.add_input('tlar:cruise_Mach', val=0.78)
        self.add_input('geometry:ht_sweep_25', val=28.)
        
        self.add_output('aerodynamics:Cl_alpha_ht', val=6.28)
        
        self.declare_partials('aerodynamics:Cl_alpha_ht', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        cruise_Mach = inputs['tlar:cruise_Mach']
        lambda_ht = inputs['geometry:ht_aspect_ratio']
        sweep_25_ht = inputs['geometry:ht_sweep_25']
        
        beta = math.sqrt(1 - cruise_Mach**2)
        cl_alpha_ht = 0.8 * 2 * math.pi * lambda_ht / \
            (2 + math.sqrt(4 + lambda_ht**2 * beta**2 / 0.95 **
                           2 * (1 + (math.tan(sweep_25_ht / 180. * math.pi))**2 / beta**2)))
            
        outputs['aerodynamics:Cl_alpha_ht'] = cl_alpha_ht