"""
Estimation of paint weight
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


class PaintWeight(ExplicitComponent):
    """ Paint weight estimation (A7) """

    def setup(self):
        self.add_input('geometry:S_total', val=np.nan, units="m**2")
        self.add_input('kfactors_a7:K_A7', val=1.)
        self.add_input('kfactors_a7:offset_A7', val=0., units="kg")

        self.add_output('weight_airframe:A7', units="kg")

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        total_wet_surface = inputs['geometry:S_total']
        k_a7 = inputs['kfactors_a7:K_A7']
        offset_a7 = inputs['kfactors_a7:offset_A7']

        temp_a7 = 0.180 * total_wet_surface
        outputs['weight_airframe:A7'] = k_a7 * temp_a7 + offset_a7
