"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import math

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeHTSweep(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:ht_root_chord', val=4.5)
        self.add_input('geometry:ht_tip_chord', val=1.5)
        self.add_input('geometry:ht_span', val=12.)
        self.add_input('geometry:ht_sweep_25', val=28.)        
        
        self.add_output('geometry:ht_sweep_0', val=33.)
        self.add_output('geometry:ht_sweep_100', val=9.)
        
        self.declare_partials('geometry:ht_sweep_0', '*', method=deriv_method)
        self.declare_partials('geometry:ht_sweep_100', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        b_h = inputs['geometry:ht_span']
        root_chord = inputs['geometry:ht_root_chord']
        tip_chord = inputs['geometry:ht_tip_chord']
        sweep_25_ht = inputs['geometry:ht_sweep_25']
        
        half_span = b_h / 2.
        sweep_0_ht = (math.pi / 2 -
                      math.atan(half_span /
                                (0.25 * root_chord - 0.25 *
                                 tip_chord + half_span *
                                 math.tan(sweep_25_ht / 180. * math.pi)))) / math.pi * 180.
        sweep_100_ht = (math.pi / 2 - math.atan(half_span / (half_span * math.tan(
            sweep_25_ht / 180. * math.pi) - 0.75 * root_chord + 0.75 * tip_chord))) / math.pi * 180.

        outputs['geometry:ht_sweep_0'] = sweep_0_ht
        outputs['geometry:ht_sweep_100'] = sweep_100_ht