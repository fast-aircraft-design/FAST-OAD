"""
    FAST - Copyright (c) 2016 ONERA ISAE
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


class EngineWeight(ExplicitComponent):
    # ---------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ---------------------------------------------------------------
    #                                B1 - Installed engine
    # ---------------------------------------------------------------
    def setup(self):
        self.add_input('propulsion_conventional:thrust_SL', val=np.nan)
        self.add_input('geometry:engine_number', val=np.nan)
        self.add_input('kfactors_b1:K_B1', val=1.)
        self.add_input('kfactors_b1:offset_B1', val=0.)

        self.add_output('weight_propulsion:B1')

    def compute(self, inputs, outputs):
        thrust_SL = inputs['propulsion_conventional:thrust_SL']
        n_engines = inputs['geometry:engine_number']
        K_B1 = inputs['kfactors_b1:K_B1']
        offset_B1 = inputs['kfactors_b1:offset_B1']

        if thrust_SL < 80000:
            temp_B1 = 22.2e-3 * thrust_SL
        else:
            temp_B1 = 14.1e-3 * thrust_SL + 648

        temp_B1 *= n_engines * 1.55
        B1 = K_B1 * temp_B1 + offset_B1

        outputs['weight_propulsion:B1'] = B1
