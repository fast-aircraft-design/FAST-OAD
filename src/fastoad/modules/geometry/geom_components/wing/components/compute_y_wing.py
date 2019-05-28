"""
    Estimation of wing Ys (sections span)
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

class ComputeYwing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing Ys estimation """
    
    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_aspect_ratio', val=np.nan)
        self.add_input('geometry:fuselage_width_max', val=np.nan)
        self.add_input('geometry:wing_area', val=np.nan)
        self.add_input('geometry:wing_break', val=np.nan)
        
        self.add_output('geometry:wing_span')
        self.add_output('geometry:wing_y2')
        self.add_output('geometry:wing_y3')
        self.add_output('geometry:wing_y4')
        
        self.declare_partials('geometry:wing_span', ['geometry:wing_area', 'geometry:wing_aspect_ratio'], method=deriv_method)
        self.declare_partials('geometry:wing_y2', 'geometry:fuselage_width_max', method=deriv_method)
        self.declare_partials('geometry:wing_y3', ['geometry:wing_area', 'geometry:wing_aspect_ratio',
                                                'geometry:wing_break'], method=deriv_method)
        self.declare_partials('geometry:wing_y4', ['geometry:wing_area', 'geometry:wing_aspect_ratio'], method=deriv_method)
        
    def compute(self, inputs, outputs):
        lambda_wing = inputs['geometry:wing_aspect_ratio']
        wing_area = inputs['geometry:wing_area']
        wing_break = inputs['geometry:wing_break']
        width_max = inputs['geometry:fuselage_width_max']

        span = math.sqrt(lambda_wing * wing_area)

        # Wing geometry
        y4_wing = span / 2.
        y2_wing = width_max / 2.
        y3_wing = y4_wing * wing_break
    
        outputs['geometry:wing_span'] = span
        outputs['geometry:wing_y2'] = y2_wing
        outputs['geometry:wing_y3'] = y3_wing
        outputs['geometry:wing_y4'] = y4_wing