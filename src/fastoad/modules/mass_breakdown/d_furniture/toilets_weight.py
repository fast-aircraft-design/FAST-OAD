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


class ToiletsWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                     D5 - Toilet
    # ----------------------------------------------------------------
    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.ac_type = self.options['ac_type']

        self.add_input('tlar:NPAX', val=np.nan)
        self.add_input('kfactors_d5:K_D5', val=1.)
        self.add_input('kfactors_d5:offset_D5', val=0.)

        self.add_output('weight_furniture:D5')

    def compute(self, inputs, outputs):
        NPAX = inputs['tlar:NPAX']
        K_D5 = inputs['kfactors_d5:K_D5']
        offset_D5 = inputs['kfactors_d5:offset_D5']

        if self.ac_type == 1.0:
            K_toilet = 0.1
        if self.ac_type == 2.0:
            K_toilet = 0.5
        if self.ac_type == 3.0:
            K_toilet = 1.0
        if (self.ac_type == 4.0) or (self.ac_type == 5.0):
            K_toilet = 1.5
        if self.ac_type == 6.0:
            K_toilet = 0.

        temp_D5 = K_toilet * NPAX
        D5 = K_D5 * temp_D5 + offset_D5

        outputs['weight_furniture:D5'] = D5
