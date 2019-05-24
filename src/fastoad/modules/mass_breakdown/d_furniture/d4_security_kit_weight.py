"""
Estimation of security kit weight
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


class SecurityKitWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Passenger security kit weight estimation (D4) """

    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.add_input('tlar:NPAX', val=np.nan)
        self.add_input('kfactors_d4:K_D4', val=1.)
        self.add_input('kfactors_d4:offset_D4', val=0., units='kg')

        self.add_output('weight_furniture:D4', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        npax = inputs['tlar:NPAX']
        k_d4 = inputs['kfactors_d4:K_D4']
        offset_d4 = inputs['kfactors_d4:offset_D4']

        if self.options['ac_type'] == 6.0:
            outputs['weight_furniture:D4'] = 0.
        else:
            temp_d4 = 1.5 * npax
            outputs['weight_furniture:D4'] = k_d4 * temp_d4 + offset_d4
