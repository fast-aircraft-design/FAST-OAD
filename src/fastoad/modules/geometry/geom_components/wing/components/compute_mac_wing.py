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


# TODO: it would be good to have a function to compute MAC for HT, VT and WING
class ComputeMACWing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing mean aerodynamic chord estimation """

    def setup(self):

        self.add_input('geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('geometry:wing:kink:leading_edge:x', val=np.nan, units='m')
        self.add_input('geometry:wing:tip:leading_edge:x', val=np.nan, units='m')
        self.add_input('geometry:wing:root:y', val=np.nan, units='m')
        self.add_input('geometry:wing:kink:y', val=np.nan, units='m')
        self.add_input('geometry:wing:tip:y', val=np.nan, units='m')
        self.add_input('geometry:wing:root:chord', val=np.nan, units='m')
        self.add_input('geometry:wing:kink:chord', val=np.nan, units='m')
        self.add_input('geometry:wing:tip:chord', val=np.nan, units='m')

        self.add_output('geometry:wing:MAC:length', units='m')
        self.add_output('geometry:wing:root:leading_edge:x', units='m')
        self.add_output('geometry:wing:MAC:y', units='m')

        self.declare_partials('geometry:wing:MAC:length', ['geometry:wing:root:y', 'geometry:wing:kink:y',
                                                   'geometry:wing:tip:y', 'geometry:wing:root:chord',
                                                   'geometry:wing:kink:chord', 'geometry:wing:tip:chord',
                                                   'geometry:wing:area'], method='fd')
        self.declare_partials('geometry:wing:root:leading_edge:x', ['geometry:wing:kink:leading_edge:x', 'geometry:wing:tip:leading_edge:x',
                                                   'geometry:wing:root:y', 'geometry:wing:kink:y',
                                                   'geometry:wing:tip:y', 'geometry:wing:root:chord',
                                                   'geometry:wing:kink:chord', 'geometry:wing:tip:chord',
                                                   'geometry:wing:area'], method='fd')
        self.declare_partials('geometry:wing:MAC:y', ['geometry:wing:root:y', 'geometry:wing:kink:y',
                                                   'geometry:wing:tip:y', 'geometry:wing:root:chord',
                                                   'geometry:wing:kink:chord', 'geometry:wing:tip:chord',
                                                   'geometry:wing:area'], method='fd')

    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing:area']
        x3_wing = inputs['geometry:wing:kink:leading_edge:x']
        x4_wing = inputs['geometry:wing:tip:leading_edge:x']
        y2_wing = inputs['geometry:wing:root:y']
        y3_wing = inputs['geometry:wing:kink:y']
        y4_wing = inputs['geometry:wing:tip:y']
        l2_wing = inputs['geometry:wing:root:chord']
        l3_wing = inputs['geometry:wing:kink:chord']
        l4_wing = inputs['geometry:wing:tip:chord']

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

        outputs['geometry:wing:MAC:length'] = l0_wing
        outputs['geometry:wing:root:leading_edge:x'] = x0_wing
        outputs['geometry:wing:MAC:y'] = y0_wing
