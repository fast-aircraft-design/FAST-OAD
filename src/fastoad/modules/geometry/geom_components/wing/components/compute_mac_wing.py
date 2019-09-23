"""
    Estimation of wing mean aerodynamic chord
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
from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeMACWing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing mean aerodynamic chord estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:wing_x3', val=np.nan, units='m')
        self.add_input('geometry:wing_x4', val=np.nan, units='m')
        self.add_input('geometry:wing_y2', val=np.nan, units='m')
        self.add_input('geometry:wing_y3', val=np.nan, units='m')
        self.add_input('geometry:wing_y4', val=np.nan, units='m')
        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:wing_l3', val=np.nan, units='m')
        self.add_input('geometry:wing_l4', val=np.nan, units='m')

        self.add_output('geometry:wing_l0', units='m')
        self.add_output('geometry:wing_x0', units='m')
        self.add_output('geometry:wing_y0', units='m')

        self.declare_partials('geometry:wing_l0', ['geometry:wing_y2', 'geometry:wing_y3',
                                                   'geometry:wing_y4', 'geometry:wing_l2',
                                                   'geometry:wing_l3', 'geometry:wing_l4',
                                                   'geometry:wing_area'], method=deriv_method)
        self.declare_partials('geometry:wing_x0', ['geometry:wing_x3', 'geometry:wing_x4',
                                                   'geometry:wing_y2', 'geometry:wing_y3',
                                                   'geometry:wing_y4', 'geometry:wing_l2',
                                                   'geometry:wing_l3', 'geometry:wing_l4',
                                                   'geometry:wing_area'], method=deriv_method)
        self.declare_partials('geometry:wing_y0', ['geometry:wing_y2', 'geometry:wing_y3',
                                                   'geometry:wing_y4', 'geometry:wing_l2',
                                                   'geometry:wing_l3', 'geometry:wing_l4',
                                                   'geometry:wing_area'], method=deriv_method)

    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        x3_wing = inputs['geometry:wing_x3']
        x4_wing = inputs['geometry:wing_x4']
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        l2_wing = inputs['geometry:wing_l2']
        l3_wing = inputs['geometry:wing_l3']
        l4_wing = inputs['geometry:wing_l4']

        l0_wing = (3 * y2_wing * l2_wing ** 2 + (y3_wing - y2_wing) *
                   (l2_wing ** 2 + l3_wing ** 2 + l2_wing * l3_wing) + (y4_wing - y3_wing)
                   * (l3_wing ** 2 + l4_wing ** 2 + l3_wing * l4_wing)) * (2 / (3 * wing_area))

        x0_wing = (x3_wing * ((y3_wing - y2_wing) * (2 * l3_wing + l2_wing) +
                              (y4_wing - y3_wing) * (2 * l3_wing + l4_wing)) +
                   x4_wing * (y4_wing - y3_wing) * (2 * l4_wing + l3_wing)) \
            / (3 * wing_area)

        y0_wing = (3 * y2_wing ** 2 * l2_wing + (y3_wing - y2_wing) *
                   (l3_wing * (y2_wing + 2 * y3_wing) + l2_wing *
                    (y3_wing + 2 * y2_wing)) + (y4_wing - y3_wing) *
                   (l4_wing
                    * (y3_wing + 2 * y4_wing) + l3_wing * (y4_wing + 2 * y3_wing))) / \
            (3 * wing_area)

        outputs['geometry:wing_l0'] = l0_wing
        outputs['geometry:wing_x0'] = x0_wing
        outputs['geometry:wing_y0'] = y0_wing
