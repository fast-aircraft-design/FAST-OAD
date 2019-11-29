"""
    Estimation of vertical tail volume coefficient
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


class ComputeVTVolCoeff(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail volume coefficient estimation """

    def setup(self):

        self.add_input('geometry:vertical_tail:area', val=np.nan, units='m**2')
        self.add_input('geometry:vertical_tail:distance_from_wing', val=np.nan, units='m')
        self.add_input('geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('geometry:wing:span', val=np.nan, units='m')

        self.add_output('geometry:vertical_tail:volume_coefficient')

        self.declare_partials('geometry:vertical_tail:volume_coefficient', '*', method='fd')

    def compute(self, inputs, outputs):
        outputs['geometry:vertical_tail:volume_coefficient'] = inputs['geometry:vertical_tail:area'] * \
                                           inputs['geometry:vertical_tail:distance_from_wing'] / \
                                           (inputs['geometry:wing:area'] * \
                                            inputs['geometry:wing:span'])
