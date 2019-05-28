"""
    Estimation of wing chords (l2 and l3)
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import numpy as np
import math 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeL2AndL3Wing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing chords (l2 and l3) estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_span', val=np.nan)
        self.add_input('geometry:wing_sweep_25', val=np.nan)
        self.add_input('geometry:wing_l1', val=np.nan)
        self.add_input('geometry:wing_l4', val=np.nan)
        self.add_input('geometry:wing_y2', val=np.nan)
        self.add_input('geometry:wing_y3', val=np.nan)
        self.add_input('geometry:wing_y4', val=np.nan)
        self.add_input('geometry:wing_taper_ratio', val=np.nan)
        self.add_input('geometry:fuselage_width_max', val=np.nan)
        
        self.add_output('geometry:wing_l2')
        self.add_output('geometry:wing_l3')
        
        self.declare_partials('geometry:wing_l2', ['geometry:wing_l1', 'geometry:wing_y2',
                                                   'geometry:wing_y3', 'geometry:wing_taper_ratio', 
                                                   'geometry:wing_span', 'geometry:fuselage_width_max',
                                                   'geometry:wing_sweep_25'], method=deriv_method)
        self.declare_partials('geometry:wing_l3', ['geometry:wing_l1', 'geometry:wing_l4', 'geometry:wing_y2',
                                                   'geometry:wing_y3', 'geometry:wing_y4'], method=deriv_method)
        
    def compute(self, inputs, outputs):
        l1_wing = inputs['geometry:wing_l1']
        l4_wing = inputs['geometry:wing_l4']
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        span = inputs['geometry:wing_span']
        width_max = inputs['geometry:fuselage_width_max']
        taper_ratio = inputs['geometry:wing_taper_ratio']
        sweep_25 = inputs['geometry:wing_sweep_25']
        
        l2_wing = (l1_wing +
                   (y3_wing -
                    y2_wing) *
                   (math.tan(sweep_25 / 180. * math.pi) -
                    3. / 2. * (1. - taper_ratio) / (span - width_max) * l1_wing))

        l3_wing = l4_wing + (l1_wing - l4_wing) * \
            (y4_wing - y3_wing) / (y4_wing - y2_wing)
            
        outputs['geometry:wing_l2'] = l2_wing
        outputs['geometry:wing_l3'] = l3_wing
        
