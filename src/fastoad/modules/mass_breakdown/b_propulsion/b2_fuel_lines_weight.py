"""
Estimation of fuel lines weight
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


class FuelLinesWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Fuel lines weight estimation (B2) """

    def setup(self):
        self.add_input('geometry:wing_b_50', val=np.nan, units="m")
        self.add_input('weight:MFW', val=np.nan, units="kg")
        self.add_input('weight_propulsion:B1', val=np.nan, units="kg")
        self.add_input('kfactors_b2:K_B2', val=1.)
        self.add_input('kfactors_b2:offset_B2', val=0., units="kg")

        self.add_output('weight_propulsion:B2', units="kg")

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        b_50 = inputs['geometry:wing_b_50']
        mfw = inputs['weight:MFW']
        k_b2 = inputs['kfactors_b2:K_B2']
        offset_b2 = inputs['kfactors_b2:offset_B2']
        weight_engines = inputs['weight_propulsion:B1']

        temp_b2 = 0.02 * weight_engines + 2.0 * b_50 + 0.35 * mfw ** 0.66
        outputs['weight_propulsion:B2'] = k_b2 * temp_b2 + offset_b2
