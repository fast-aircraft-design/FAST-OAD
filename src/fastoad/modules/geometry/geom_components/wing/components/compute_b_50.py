"""
    Estimation of wing B50
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
import math
import numpy as np

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeB50(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing B50 estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_x4', val=np.nan, units='m')
        self.add_input('geometry:wing_y2', val=np.nan, units='m')
        self.add_input('geometry:wing_y4', val=np.nan, units='m')
        self.add_input('geometry:wing_l1', val=np.nan, units='m')
        self.add_input('geometry:wing_l4', val=np.nan, units='m')
        self.add_input('geometry:wing_span', val=np.nan, units='m')

        self.add_output('geometry:wing_b_50', units='m')

        self.declare_partials('geometry:wing_b_50', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        x4_wing = inputs['geometry:wing_x4']
        y2_wing = inputs['geometry:wing_y2']
        y4_wing = inputs['geometry:wing_y4']
        l1_wing = inputs['geometry:wing_l1']
        l4_wing = inputs['geometry:wing_l4']
        span = inputs['geometry:wing_span']

        sweep_50 = math.atan(
            (x4_wing + l4_wing * 0.5 - 0.5 * l1_wing) / (y4_wing - y2_wing))
        b_50 = span / math.cos(sweep_50)

        outputs['geometry:wing_b_50'] = b_50
