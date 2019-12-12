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

    def setup(self):

        self.add_input('geometry:wing:root:chord', val=np.nan, units='m')
        self.add_input('geometry:wing:root:y', val=np.nan, units='m')
        self.add_input('geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('geometry:fuselage:maximum_width', val=np.nan, units='m')

        self.add_output('geometry:wing:outer_area', units='m**2')
        self.add_output('geometry:wing:wetted_area', units='m**2')

        self.declare_partials('geometry:wing:outer_area', ['geometry:wing:area',
                                                           'geometry:wing:root:y',
                                                           'geometry:wing:root:chord'],
                              method='fd')
        self.declare_partials('geometry:wing:wetted_area', ['geometry:wing:area',
                                                            'geometry:wing:root:chord',
                                                            'geometry:fuselage:maximum_width'],
                              method='fd')

    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing:area']
        l2_wing = inputs['geometry:wing:root:chord']
        y2_wing = inputs['geometry:wing:root:y']
        width_max = inputs['geometry:fuselage:maximum_width']

        s_pf = wing_area - 2 * l2_wing * y2_wing
        wet_area_wing = 2 * (wing_area - width_max * l2_wing)

        outputs['geometry:wing:outer_area'] = s_pf
        outputs['geometry:wing:wetted_area'] = wet_area_wing
