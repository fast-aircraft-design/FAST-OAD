"""
Estimation of flight kit weight
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
from openmdao.core.explicitcomponent import ExplicitComponent


class FlightKitWeight(ExplicitComponent):
    """ Flight kit weight estimation (C6) """

    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.add_input('kfactors_c6:K_C6', val=1.)
        self.add_input('kfactors_c6:offset_C6', val=0., units='kg')

        self.add_output('weight_systems:C6', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        k_c6 = inputs['kfactors_c6:K_C6']
        offset_c6 = inputs['kfactors_c6:offset_C6']

        if self.options['ac_type'] == 1.0:
            temp_c6 = 10.0
        else:
            temp_c6 = 45.0

        outputs['weight_systems:C6'] = k_c6 * temp_c6 + offset_c6
