"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeVTDistance(ExplicitComponent):
    
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

        self.add_output('geometry:vt_lp', val=18.)
        self.add_output('k_ar_effective', val=1.55)
        
        self.declare_partials('geometry:vt_lp', ['geometry:fuselage_length', 'geometry:wing_position'], method=deriv_method)

    def compute(self, inputs, outputs):
        fus_length = inputs['geometry:fuselage_length']
        fa_length = inputs['geometry:wing_position']

        if self.tail_type == 1.0:
            if self.ac_family == 1.0:
                lp_vt = 0.93 * fus_length - fa_length
                k_ar_effective = 2.9
            elif self.ac_family == 2.0:
                lp_vt = 6.6
                k_ar_effective = 2.9
        else:    
            lp_vt = 0.88 * fus_length - fa_length
            k_ar_effective = 1.55
            
        outputs['geometry:vt_lp'] = lp_vt
        outputs['k_ar_effective'] = k_ar_effective