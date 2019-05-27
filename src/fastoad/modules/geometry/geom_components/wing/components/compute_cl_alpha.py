"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeCLalpha(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('tlar:cruise_Mach', val=0.78)
        self.add_input('geometry:fuselage_width_max', val=4.)
        self.add_input('geometry:fuselage_height_max', val=4.)
        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:wing_l2', val=6.)
        self.add_input('geometry:wing_l4', val=1.5)
        self.add_input('geometry:wing_toc_tip', val=0.1)
        self.add_input('geometry:wing_sweep_25', val=25.)
        self.add_input('geometry:wing_aspect_ratio', val=9.48)
        self.add_input('geometry:wing_span', val=32.)
        
        self.add_output('aerodynamics:Cl_alpha')
        
        self.declare_partials('aerodynamics:Cl_alpha', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        cruise_Mach = inputs['tlar:cruise_Mach']
        width_max = inputs['geometry:fuselage_width_max']
        height_max = inputs['geometry:fuselage_height_max']
        span = inputs['geometry:wing_span']
        lambda_wing = inputs['geometry:wing_aspect_ratio']
        el_ext = inputs['geometry:wing_toc_tip']
        wing_area = inputs['geometry:wing_area']
        l2_wing = inputs['geometry:wing_l2']
        l4_wing = inputs['geometry:wing_l4']
        sweep_25 = inputs['geometry:wing_sweep_25']
        
        beta = math.sqrt(1 - cruise_Mach**2)
        d_f = math.sqrt(width_max * height_max)
        fact_F = 1.07 * (1 + d_f / span)**2
        lambda_wing_eff = lambda_wing * (1 + 1.9 * l4_wing * el_ext / span)
        cl_alpha_wing = 2 * math.pi * lambda_wing_eff / \
            (2 + math.sqrt(4 + lambda_wing_eff**2 * beta**2 / 0.95**2 * (
                1 + (math.tan(sweep_25 / 180. * math.pi))**2 / beta**2))) * \
            (wing_area - l2_wing * width_max) / wing_area * fact_F
            
        outputs['aerodynamics:Cl_alpha'] = cl_alpha_wing
        