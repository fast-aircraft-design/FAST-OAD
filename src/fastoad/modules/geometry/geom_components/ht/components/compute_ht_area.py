"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeHTArea(ExplicitComponent):
    
    def initialize(self):
        self.options.declare('deriv_method', default='fd')

        self.options.declare('ac_family', types=float, default=1.)
        self.options.declare('tail_type', types=float, default=0.)
        
    def setup(self):
        deriv_method = self.options['deriv_method']

        self.ac_family = self.options['ac_family']
        self.tail_type = self.options['tail_type']
        
        self.add_input('geometry:fuselage_length', val=37.)
        self.add_input('geometry:wing_position', val=16.)
        self.add_input('geometry:ht_vol_coeff', val=1.)
        self.add_input('geometry:wing_l0', val=4.2)
        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:ht_area', val=70.)
        
        self.add_output('geometry:ht_lp', val=16.)
        self.add_output('geometry:ht_wet_area', val=140.)
        self.add_output('delta_cm_takeoff', val=0.)
        
        self.declare_partials('geometry:ht_lp', ['geometry:fuselage_length', 'geometry:wing_position'], method=deriv_method)
        self.declare_partials('geometry:ht_wet_area', 'geometry:ht_area', method=deriv_method)     
        self.declare_partials('delta_cm_takeoff', '*', method=deriv_method)
            
    def compute(self, inputs, outputs):
        fus_length = inputs['geometry:fuselage_length']
        fa_length = inputs['geometry:wing_position']
        wing_area = inputs['geometry:wing_area']
        l0_wing = inputs['geometry:wing_l0']
        s_h = inputs['geometry:ht_area']
        ht_vol_coeff = inputs['geometry:ht_vol_coeff']

        if self.tail_type == 1.0:
            if self.ac_family == 1.0:
                lp_ht = fus_length - fa_length
            elif self.ac_family == 2.0:
                lp_ht = 7.7 
        else:
            lp_ht = 0.91 * fus_length - fa_length           

        if self.tail_type == 0.:
            wet_area_ht = 2 * s_h
        elif self.tail_type == 1.:
            wet_area_ht = 2 * 0.8 * s_h
        else:
            print('Error in the tailplane positioning')
        
        outputs['geometry:ht_lp'] = lp_ht
        outputs['geometry:ht_wet_area'] = wet_area_ht
        outputs['delta_cm_takeoff'] = s_h * lp_ht / wing_area / l0_wing - ht_vol_coeff