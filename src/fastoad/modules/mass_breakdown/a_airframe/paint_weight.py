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


class PaintWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                                A7 - Paint
    # ---------------------------------------------------------------
    def setup(self):
        self.add_input('geometry:S_total', val=np.nan)
        self.add_input('kfactors_a7:K_A7', val=1.)
        self.add_input('kfactors_a7:offset_A7', val=0.)

        self.add_output('weight_airframe:A7')

    def compute(self, inputs, outputs):
        S_total = inputs['geometry:S_total']
        K_A7 = inputs['kfactors_a7:K_A7']
        offset_A7 = inputs['kfactors_a7:offset_A7']

        temp_A7 = 0.180 * S_total
        A7 = K_A7 * temp_A7 + offset_A7

        outputs['weight_airframe:A7'] = A7
