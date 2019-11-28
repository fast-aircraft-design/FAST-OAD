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
import math
import numpy as np

from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeYWing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing Ys estimation """

    def setup(self):

        self.add_input('geometry:wing:aspect_ratio', val=np.nan)
        self.add_input('geometry:fuselage:maximum_width', val=np.nan, units='m')
        self.add_input('geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('geometry:wing:break', val=np.nan)

        self.add_output('geometry:wing:span', units='m')
        self.add_output('geometry:wing:root:y', units='m')
        self.add_output('geometry:wing:kink:y', units='m')
        self.add_output('geometry:wing:tip:y', units='m')

        self.declare_partials('geometry:wing:span', ['geometry:wing:area',
                                                     'geometry:wing:aspect_ratio'],
                              method='fd')
        self.declare_partials('geometry:wing:root:y', 'geometry:fuselage:maximum_width',
                              method='fd')
        self.declare_partials('geometry:wing:kink:y', ['geometry:wing:area',
                                                   'geometry:wing:aspect_ratio',
                                                   'geometry:wing:break'],
                              method='fd')
        self.declare_partials('geometry:wing:tip:y', ['geometry:wing:area',
                                                   'geometry:wing:aspect_ratio'],
                              method='fd')

    def compute(self, inputs, outputs):
        lambda_wing = inputs['geometry:wing:aspect_ratio']
        wing_area = inputs['geometry:wing:area']
        wing_break = inputs['geometry:wing:break']
        width_max = inputs['geometry:fuselage:maximum_width']

        span = math.sqrt(lambda_wing * wing_area)

        # Wing geometry
        y4_wing = span / 2.
        y2_wing = width_max / 2.
        y3_wing = y4_wing * wing_break

        outputs['geometry:wing:span'] = span
        outputs['geometry:wing:root:y'] = y2_wing
        outputs['geometry:wing:kink:y'] = y3_wing
        outputs['geometry:wing:tip:y'] = y4_wing
