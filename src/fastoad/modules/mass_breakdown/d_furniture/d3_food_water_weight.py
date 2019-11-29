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

from fastoad.modules.mass_breakdown.options import AIRCRAFT_TYPE_OPTION


class FoodWaterWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Passenger food water weight estimation (D3) """

    def initialize(self):
        self.options.declare(AIRCRAFT_TYPE_OPTION, types=float, default=2.0)

    def setup(self):
        self.add_input('TLAR:NPAX', val=np.nan)
        self.add_input('weight:furniture:food_water:mass:k', val=1.)
        self.add_input('weight:furniture:food_water:mass:offset', val=0., units='kg')

        self.add_output('weight:furniture:food_water:mass', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        npax = inputs['TLAR:NPAX']
        k_d3 = inputs['weight:furniture:food_water:mass:k']
        offset_d3 = inputs['weight:furniture:food_water:mass:offset']

        if self.options[AIRCRAFT_TYPE_OPTION] == 6.0:
            outputs['weight:furniture:food_water:mass'] = 0.
        else:
            temp_d3 = 8.75 * npax
            outputs['weight:furniture:food_water:mass'] = k_d3 * temp_d3 + offset_d3
