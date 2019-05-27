"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeVTMAC(ExplicitComponent):

deriv_method


    def setup(self):
        self.add_input('geometry:vt_root_chord', val=6.)
        self.add_input('geometry:vt_tip_chord', val=2.)
        self.add_input('geometry:vt_sweep_25', val=35.)
        self.add_input('geometry:vt_span', val=8.)
    
        self.add_output('geometry:vt_length', val=3.5)
        self.add_output('geometry:vt_x0', val=20.)
        self.add_output('geometry:vt_z0', val=2.5)

        self.declare_partials('geometry:vt_length', ['geometry:vt_root_chord', 'geometry:vt_tip_chord'])
        self.declare_partials('geometry:vt_x0', '*', method='fd')
        self.declare_partials('geometry:vt_z0', ['geometry:vt_root_chord', 'geometry:vt_tip_chord',
                                                 'geometry:vt_span'])
        
    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:vt_root_chord']
        tip_chord = inputs['geometry:vt_tip_chord']
        sweep_25_vt = inputs['geometry:vt_sweep_25']
        b_v = inputs['geometry:vt_span']
    
        tmp = (root_chord * 0.25 + b_v * math.tan(sweep_25_vt / 180. * math.pi) - tip_chord * 0.25)
        
        mac_vt = (root_chord**2 + root_chord * tip_chord + tip_chord**2) / \
            (tip_chord + root_chord) * 2. / 3.
        x0_vt = (tmp * (root_chord + 2 * tip_chord)) / \
            (3 * (root_chord + tip_chord))
        z0_vt = (2 * b_v * (0.5 * root_chord + tip_chord)) / \
            (3 * (root_chord + tip_chord))
            
        outputs['geometry:vt_length'] = mac_vt
        outputs['geometry:vt_x0'] = x0_vt
        outputs['geometry:vt_z0'] = z0_vt

    def compute_partials(self, inputs, partials):
        root_chord = inputs['geometry:vt_root_chord']
        tip_chord = inputs['geometry:vt_tip_chord']
        sweep_25_vt = inputs['geometry:vt_sweep_25']
        b_v = inputs['geometry:vt_span']

        tmp = (root_chord * 0.25 + b_v *
                 math.tan(sweep_25_vt / math.pi * 180.) - tip_chord * 0.25)
        dtmp_dcr = 0.25 
        dtmp_dct = -0.25
        dtmp_dspan =  math.tan(sweep_25_vt / 180. * math.pi)
        dtmp_dsweep = b_v * math.pi / 180. / (math.cos(sweep_25_vt / 180. * math.pi))**2   
        
        num = root_chord**2 + root_chord * tip_chord + tip_chord**2
        den = tip_chord + root_chord
        
        dnum_dcr = 2 * root_chord + tip_chord
        dnum_dct = root_chord + 2 * tip_chord
        dden_dcr = 1.
        dden_dct = 1.

        partials['geometry:vt_length', 'geometry:vt_root_chord'] = 2./3. * (dnum_dcr * den - num * dden_dcr) / den**2
        partials['geometry:vt_length', 'geometry:vt_tip_chord'] = 2./3. * (dnum_dct * den - num * dden_dct) / den**2
        tmp1 = (root_chord + 2 * tip_chord)
        num = tmp * tmp1
        den *= 3.
        dnum_dcr = dtmp_dcr * tmp1 + tmp
        dnum_dct = dtmp_dct * tmp1 + 2 * tmp
        dden_dcr *= 3.
        dden_dct *= 3.

        partials['geometry:vt_x0', 'geometry:vt_root_chord'] = (dnum_dcr * den - num * dden_dcr) / den**2
        partials['geometry:vt_x0', 'geometry:vt_tip_chord'] = (dnum_dct * den - num * dden_dct) / den**2
        partials['geometry:vt_x0', 'geometry:vt_span'] = dtmp_dspan * (root_chord + 2 * tip_chord) / den
        partials['geometry:vt_x0', 'geometry:vt_sweep_25'] = dtmp_dsweep * (root_chord + 2 * tip_chord) / den
        
        num = 2 * b_v * (0.5 * root_chord + tip_chord)
        
        dnum_dcr = 2 * b_v * 0.5
        dnum_dct = 2 * b_v

        partials['geometry:vt_z0', 'geometry:vt_root_chord'] = (dnum_dcr * den - num * dden_dcr) / den**2
        partials['geometry:vt_z0', 'geometry:vt_tip_chord'] = (dnum_dct * den - num * dden_dct) / den**2
        partials['geometry:vt_z0', 'geometry:vt_span'] = 2 * (0.5 * root_chord + tip_chord) / den