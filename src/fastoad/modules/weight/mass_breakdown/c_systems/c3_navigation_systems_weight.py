"""
Estimation of navigation systems weight
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

from fastoad.modules.options import AIRCRAFT_TYPE_OPTION


class NavigationSystemsWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Navigation systems weight estimation (C3) """

    def initialize(self):
        self.options.declare(AIRCRAFT_TYPE_OPTION, types=float, default=2.0)

    def setup(self):
        self.add_input('geometry:fuselage:length', val=np.nan, units='m')
        self.add_input('geometry:wing:b_50', val=np.nan, units='m')
        self.add_input('weight:systems:navigation:mass:k', val=1.)
        self.add_input('weight:systems:navigation:mass:offset', val=0., units='kg')

        self.add_output('weight:systems:navigation:mass', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        fuselage_length = inputs['geometry:fuselage:length']
        b_50 = inputs['geometry:wing:b_50']
        k_c3 = inputs['weight:systems:navigation:mass:k']
        offset_c3 = inputs['weight:systems:navigation:mass:offset']

        aircraft_type = self.options[AIRCRAFT_TYPE_OPTION]
        if aircraft_type == 1.0:
            base_weight = 150
        elif aircraft_type == 2.0:
            base_weight = 450
        elif aircraft_type == 3.0:
            base_weight = 700
        elif aircraft_type in [4.0, 5.0]:
            base_weight = 800
        else:
            raise ValueError("Unexpected aircraft type")

        temp_c3 = base_weight + 0.033 * fuselage_length * b_50
        outputs['weight:systems:navigation:mass'] = k_c3 * temp_c3 + offset_c3
