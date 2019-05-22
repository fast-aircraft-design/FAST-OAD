"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

#      This file is part of FAST : A framework for rapid Overall Aircraft Design
#      Copyright (C) 2019  ONERA/ISAE
#      FAST is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class UnconsumablesWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                                B3 - unconsumables
    # ---------------------------------------------------------------
    def setup(self):
        self.add_input('geometry:engine_number', val=np.nan)
        self.add_input('weight:MFW', val=np.nan)
        self.add_input('kfactors_b3:K_B3', val=1.)
        self.add_input('kfactors_b3:offset_B3', val=0.)

        self.add_output('weight_propulsion:B3')

    def compute(self, inputs, outputs):
        n_engines = inputs['geometry:engine_number']
        MFW = inputs['weight:MFW']
        K_B3 = inputs['kfactors_b3:K_B3']
        offset_B3 = inputs['kfactors_b3:offset_B3']

        temp_B3 = 25 * n_engines + 0.0035 * MFW
        B3 = K_B3 * temp_B3 + offset_B3

        outputs['weight_propulsion:B3'] = B3
