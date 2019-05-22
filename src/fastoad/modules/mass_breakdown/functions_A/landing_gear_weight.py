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


class LandingGearWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                                A5 - LG
    # ---------------------------------------------------------------
    def setup(self):
        self.add_input('weight:MTOW', val=np.nan)
        self.add_input('kfactors_a5:K_A5', val=1.)
        self.add_input('kfactors_a5:offset_A5', val=0.)

        self.add_output('weight_airframe:A51')
        self.add_output('weight_airframe:A52')

    def compute(self, inputs, outputs):
        MTOW = inputs['weight:MTOW']
        K_A5 = inputs['kfactors_a5:K_A5']
        offset_A5 = inputs['kfactors_a5:offset_A5']

        temp_A51 = 18.1 + 0.131 * MTOW ** 0.75 + 0.019 * MTOW + 2.23E-5 * MTOW ** 1.5
        temp_A52 = 9.1 + 0.082 * MTOW ** 0.75 + 2.97E-6 * MTOW ** 1.5

        A51 = K_A5 * temp_A51 + offset_A5
        A52 = K_A5 * temp_A52 + offset_A5

        outputs['weight_airframe:A51'] = A51
        outputs['weight_airframe:A52'] = A52
