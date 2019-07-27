"""
    Estimation of wing Xs
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

class ComputeXWing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing Xs estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_l1', val=np.nan, units='m')
        self.add_input('geometry:wing_l3', val=np.nan, units='m')
        self.add_input('geometry:wing_l4', val=np.nan, units='m')
        self.add_input('geometry:wing_y2', val=np.nan, units='m')
        self.add_input('geometry:wing_y3', val=np.nan, units='m')
        self.add_input('geometry:wing_y4', val=np.nan, units='m')
        self.add_input('geometry:wing_sweep_25', val=np.nan, units='deg')
        
        self.add_output('geometry:wing_x3', units='m')
        self.add_output('geometry:wing_x4', units='m')
        
        self.declare_partials('geometry:wing_x3', ['geometry:wing_l1', 'geometry:wing_y2',
                                                   'geometry:wing_y3', 'geometry:wing_l3',
                                                   'geometry:wing_sweep_25'], method=deriv_method)
        self.declare_partials('geometry:wing_x4', ['geometry:wing_l1', 'geometry:wing_y2',
                                                   'geometry:wing_y4', 'geometry:wing_l4',
                                                   'geometry:wing_sweep_25'], method=deriv_method)
        
    def compute(self, inputs, outputs):
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        l1_wing = inputs['geometry:wing_l1']
        l3_wing = inputs['geometry:wing_l3']
        l4_wing = inputs['geometry:wing_l4']
        sweep_25 = inputs['geometry:wing_sweep_25']
    
        x3_wing = 1. / 4. * l1_wing + \
            (y3_wing - y2_wing) * \
            math.tan(sweep_25 / 180. * math.pi) - 1. / 4. * l3_wing
        x4_wing = 1. / 4. * l1_wing + \
            (y4_wing - y2_wing) * \
            math.tan(sweep_25 / 180. * math.pi) - 1. / 4. * l4_wing
            
        outputs['geometry:wing_x3'] = x3_wing
        outputs['geometry:wing_x4'] = x4_wing
        
 