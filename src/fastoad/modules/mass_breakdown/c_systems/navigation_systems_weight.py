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


class NavigationSystemsWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                     C3 - Instruments & Navigation
    # ----------------------------------------------------------------
    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.ac_type = self.options['ac_type']

        self.add_input('geometry:fuselage_length', val=np.nan)
        self.add_input('geometry:wing_b_50', val=np.nan)
        self.add_input('kfactors_c3:K_C3', val=1.)
        self.add_input('kfactors_c3:offset_C3', val=0.)

        self.add_output('weight_systems:C3')

    def compute(self, inputs, outputs):
        fus_length = inputs['geometry:fuselage_length']
        b_50 = inputs['geometry:wing_b_50']
        K_C3 = inputs['kfactors_c3:K_C3']
        offset_C3 = inputs['kfactors_c3:offset_C3']

        if self.ac_type == 1.0:
            K_IN = 150
        if self.ac_type == 2.0:
            K_IN = 450
        if self.ac_type == 3.0:
            K_IN = 700
        if self.ac_type == 4.0:
            K_IN = 800
        if self.ac_type == 5.0:
            K_IN = 800

        temp_C3 = K_IN + 0.033 * fus_length * b_50
        C3 = K_C3 * temp_C3 + offset_C3

        outputs['weight_systems:C3'] = C3
