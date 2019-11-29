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
import math
import numpy as np

from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeL2AndL3Wing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing chords (l2 and l3) estimation """

    def setup(self):

        self.add_input('geometry:wing:span', val=np.nan, units='m')
        self.add_input('geometry:wing:sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:wing:l1', val=np.nan, units='m')
        self.add_input('geometry:wing:tip:chord', val=np.nan, units='m')
        self.add_input('geometry:wing:root:y', val=np.nan, units='m')
        self.add_input('geometry:wing:kink:y', val=np.nan, units='m')
        self.add_input('geometry:wing:tip:y', val=np.nan, units='m')
        self.add_input('geometry:wing:taper_ratio', val=np.nan)
        self.add_input('geometry:fuselage:maximum_width', val=np.nan, units='m')

        self.add_output('geometry:wing:root:chord', units='m')
        self.add_output('geometry:wing:kink:chord', units='m')

        self.declare_partials('geometry:wing:root:chord', ['geometry:wing:l1',
                                                   'geometry:wing:root:y',
                                                   'geometry:wing:kink:y',
                                                   'geometry:wing:taper_ratio',
                                                   'geometry:wing:span',
                                                   'geometry:fuselage:maximum_width',
                                                   'geometry:wing:sweep_25'],
                              method='fd')
        self.declare_partials('geometry:wing:kink:chord', ['geometry:wing:l1',
                                                   'geometry:wing:tip:chord',
                                                   'geometry:wing:root:y',
                                                   'geometry:wing:kink:y',
                                                   'geometry:wing:tip:y'],
                              method='fd')

    def compute(self, inputs, outputs):
        l1_wing = inputs['geometry:wing:l1']
        l4_wing = inputs['geometry:wing:tip:chord']
        y2_wing = inputs['geometry:wing:root:y']
        y3_wing = inputs['geometry:wing:kink:y']
        y4_wing = inputs['geometry:wing:tip:y']
        span = inputs['geometry:wing:span']
        width_max = inputs['geometry:fuselage:maximum_width']
        taper_ratio = inputs['geometry:wing:taper_ratio']
        sweep_25 = inputs['geometry:wing:sweep_25']

        l2_wing = (l1_wing +
                   (y3_wing -
                    y2_wing) *
                   (math.tan(sweep_25 / 180. * math.pi) -
                    3. / 2. * (1. - taper_ratio) / (span - width_max) * l1_wing))

        l3_wing = l4_wing + (l1_wing - l4_wing) * \
                  (y4_wing - y3_wing) / (y4_wing - y2_wing)

        outputs['geometry:wing:root:chord'] = l2_wing
        outputs['geometry:wing:kink:chord'] = l3_wing
