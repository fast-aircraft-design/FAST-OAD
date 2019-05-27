"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from fast.atmosphere import atmosphere

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeHTVolCoeff(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('cg_airframe:A51', val=16.)
        self.add_input('cg_airframe:A52', val=3.)
        self.add_input('weight:MTOW', val=74000.)
        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:wing_l0', val=4.2)
        self.add_input('cg:required_cg_range', val=0.3)
        
        self.add_output('delta_lg', val=13.)
        self.add_output('geometry:ht_vol_coeff', val=1.)
        
        self.declare_partials('delta_lg', ['cg_airframe:A51', 'cg_airframe:A52'], method=deriv_method)
        self.declare_partials('geometry:ht_vol_coeff', '*', method=deriv_method)
    
    def compute(self, inputs, outputs):
        cg_A51 = inputs['cg_airframe:A51']
        cg_A52 = inputs['cg_airframe:A52']
        mtow = inputs['weight:MTOW']
        wing_area = inputs['geometry:wing_area']
        l0_wing = inputs['geometry:wing_l0']
        required_cg_range = inputs['cg:required_cg_range']
        
        delta_lg = cg_A51 - cg_A52
        temperature, rho, pression, viscosity, sos = atmosphere(0)
        vspeed = sos * 0.2  # assume the corresponding Mach of VR is 0.2

        cm_wheel = 0.08 * delta_lg * mtow * 9.81 / \
            (0.5 * rho * vspeed**2 * wing_area * l0_wing)
        delta_cm = mtow * l0_wing * required_cg_range * \
            9.81 / (0.5 * rho * vspeed**2 * wing_area * l0_wing)
        ht_vol_coeff = cm_wheel + delta_cm
        outputs['delta_lg'] = delta_lg
        outputs['geometry:ht_vol_coeff'] = ht_vol_coeff