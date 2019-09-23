"""
    Estimation of wing wet area
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


class ComputeWetAreaWing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing wet area estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:wing_y2', val=np.nan, units='m')
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:fuselage_width_max', val=np.nan, units='m')

        self.add_output('geometry:wing_area_pf')
        self.add_output('geometry:wing_wet_area', units='m**2')

        self.declare_partials('geometry:wing_area_pf', ['geometry:wing_area',
                                                        'geometry:wing_y2',
                                                        'geometry:wing_l2'],
                              method=deriv_method)
        self.declare_partials('geometry:wing_wet_area', ['geometry:wing_area',
                                                         'geometry:wing_l2',
                                                         'geometry:fuselage_width_max'],
                              method=deriv_method)

    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        l2_wing = inputs['geometry:wing_l2']
        y2_wing = inputs['geometry:wing_y2']
        width_max = inputs['geometry:fuselage_width_max']

        s_pf = wing_area - 2 * l2_wing * y2_wing
        wet_area_wing = 2 * (wing_area - width_max * l2_wing)

        outputs['geometry:wing_area_pf'] = s_pf
        outputs['geometry:wing_wet_area'] = wet_area_wing
