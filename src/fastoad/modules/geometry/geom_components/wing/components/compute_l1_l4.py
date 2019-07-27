"""
    Estimation of wing chords (l1 and l4)
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

class ComputeL1AndL4Wing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing chords (l1 and l4) estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:wing_y2', val=np.nan, units='m')
        self.add_input('geometry:wing_y3', val=np.nan, units='m')
        self.add_input('geometry:wing_span', val=np.nan, units='m')
        self.add_input('geometry:fuselage_width_max', val=np.nan, units='m')
        self.add_input('geometry:wing_taper_ratio', val=np.nan)
        self.add_input('geometry:wing_sweep_25', val=np.nan, units='deg')
        
        self.add_output('geometry:wing_l1', units='m')
        self.add_output('geometry:wing_l4', units='m')
        
        self.declare_partials('geometry:wing_l1', '*', method=deriv_method)
        self.declare_partials('geometry:wing_l4', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        sweep_25 = inputs['geometry:wing_sweep_25']
        width_max = inputs['geometry:fuselage_width_max']
        taper_ratio = inputs['geometry:wing_taper_ratio']
        
        l1_wing = (wing_area - (y3_wing - y2_wing) * (y3_wing + y2_wing) *
                   math.tan(sweep_25 / 180. * math.pi)) / \
                   ((1. + taper_ratio) / 2. * (span - width_max) + width_max - \
                    (3. * (1. - taper_ratio) * (y3_wing - y2_wing) * (y3_wing + y2_wing))
                    / (2. * (span - width_max)))
        
        l4_wing = l1_wing * taper_ratio
        
        outputs['geometry:wing_l1'] = l1_wing
        outputs['geometry:wing_l4'] = l4_wing
        
