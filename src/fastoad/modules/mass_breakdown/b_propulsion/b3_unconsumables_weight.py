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


class UnconsumablesWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ unconsumables weight estimation (B2) """

    def setup(self):
        self.add_input('geometry:engine_number', val=np.nan)
        self.add_input('weight:MFW', val=np.nan, units='kg')
        self.add_input('kfactors_b3:K_B3', val=1.)
        self.add_input('kfactors_b3:offset_B3', val=0., units='kg')

        self.add_output('weight_propulsion:B3', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        n_engines = inputs['geometry:engine_number']
        mfw = inputs['weight:MFW']
        k_b3 = inputs['kfactors_b3:K_B3']
        offset_b3 = inputs['kfactors_b3:offset_B3']

        temp_b3 = 25 * n_engines + 0.0035 * mfw
        outputs['weight_propulsion:B3'] = k_b3 * temp_b3 + offset_b3
