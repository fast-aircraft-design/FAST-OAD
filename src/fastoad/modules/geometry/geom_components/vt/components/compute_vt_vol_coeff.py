"""
    Estimation of vertical tail volume coefficient
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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
        self.add_input('data:geometry:vertical_tail:area', val=np.nan, units='m**2')
        self.add_input('data:geometry:vertical_tail:distance_from_wing', val=np.nan, units='m')
        self.add_input('data:geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('data:geometry:wing:span', val=np.nan, units='m')

        self.add_output('data:geometry:vertical_tail:volume_coefficient')

        self.declare_partials('data:geometry:vertical_tail:volume_coefficient', '*', method='fd')

    def compute(self, inputs, outputs):
        outputs['data:geometry:vertical_tail:volume_coefficient'] = inputs[
                                                                        'data:geometry:vertical_tail:area'] * \
                                                                    inputs[
                                                                        'data:geometry:vertical_tail:distance_from_wing'] / \
                                                                    (inputs[
                                                                         'data:geometry:wing:area'] * \
                                                                     inputs[
                                                                         'data:geometry:wing:span'])
