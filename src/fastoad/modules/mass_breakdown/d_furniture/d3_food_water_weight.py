"""
Estimation of food water weight
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


class FoodWaterWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Passenger food water weight estimation (D3) """

    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.add_input('tlar:NPAX', val=np.nan)
        self.add_input('kfactors_d3:K_D3', val=1.)
        self.add_input('kfactors_d3:offset_D3', val=0., units='kg')

        self.add_output('weight_furniture:D3', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        npax = inputs['tlar:NPAX']
        k_d3 = inputs['kfactors_d3:K_D3']
        offset_d3 = inputs['kfactors_d3:offset_D3']

        if self.options['ac_type'] == 6.0:
            outputs['weight_furniture:D3'] = 0.
        else:
            temp_d3 = 8.75 * npax
            outputs['weight_furniture:D3'] = k_d3 * temp_d3 + offset_d3
