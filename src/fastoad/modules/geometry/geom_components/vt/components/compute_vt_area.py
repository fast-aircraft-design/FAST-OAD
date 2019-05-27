"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeVTArea(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

#        self.add_input('geometry:wing_position', val=16.)
        self.add_input('cg_ratio', val=0.5)
        self.add_input('geometry:wing_l0', val=4.2)
        self.add_input('dcn_beta', val=1.)
        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:wing_span', val=32.)
        self.add_input('geometry:vt_lp', val=18.)
        self.add_input('geometry:vt_area', val=45.)
        self.add_input('aerodynamics:Cl_alpha_vt', val=6.28)
        
        self.add_output('geometry:vt_wet_area', val=100.)
        self.add_output('delta_cn', val=0.)
        
        self.declare_partials('geometry:vt_wet_area', 'geometry:vt_area')

        self.declare_partials('delta_cn', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        l0_wing = inputs['geometry:wing_l0']
        x_cg_plane = inputs['cg_ratio']
        s_v = inputs['geometry:vt_area']
        dcn_beta = inputs['dcn_beta']
        cl_alpha_vt = inputs['aerodynamics:Cl_alpha_vt']
        lp_vt = inputs['geometry:vt_lp']
        
#        x_ca_vt = fa_length + lp_vt
#        x_cg_plane_aft_abs = fa_length - 0.25 * l0_wing + x_cg_plane * l0_wing   
        dxca_xcg = lp_vt + 0.25 * l0_wing - x_cg_plane * l0_wing   
        delta_cn = s_v * dxca_xcg / wing_area / span * cl_alpha_vt - dcn_beta
        wet_area_vt = 2.1 * s_v

        outputs['geometry:vt_wet_area'] = wet_area_vt
        outputs['delta_cn'] = delta_cn