"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeVTSweep(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:vt_span', val=10.)
        self.add_input('geometry:vt_root_chord', val=6.)
        self.add_input('geometry:vt_tip_chord', val=2.)
        self.add_input('geometry:vt_sweep_25', val=35.)
        
        self.add_output('geometry:vt_sweep_0', val=45.)
        self.add_output('geometry:vt_sweep_100', val=10.)
        
        self.declare_partials('geometry:vt_sweep_0', '*', method=deriv_method)
        self.declare_partials('geometry:vt_sweep_100', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:vt_root_chord']
        tip_chord = inputs['geometry:vt_tip_chord']
        sweep_25_vt = inputs['geometry:vt_sweep_25']
        b_v = inputs['geometry:vt_span']
        
        sweep_0_vt = (math.pi / 2 -
                      math.atan(b_v / (0.25 * root_chord - 0.25 *
                                       tip_chord + b_v *
                                       math.tan(sweep_25_vt / 180. * math.pi)))) / math.pi * 180.
        sweep_100_vt = (math.pi / 2 -
                        math.atan(b_v / (b_v * math.tan(sweep_25_vt /
                                                        180. * math.pi) - 0.75 *
                                         root_chord + 0.75 * tip_chord))) / math.pi * 180.

        outputs['geometry:vt_sweep_0'] = sweep_0_vt                     
        outputs['geometry:vt_sweep_100'] = sweep_100_vt