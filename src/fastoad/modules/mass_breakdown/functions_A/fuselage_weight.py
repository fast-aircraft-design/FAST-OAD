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
from math import sqrt
from openmdao.core.explicitcomponent import ExplicitComponent


class FuselageWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                                A2 - Fuselage
    # ---------------------------------------------------------------
    def setup(self):
        self.add_input('geometry:fuselage_wet_area', val=np.nan)
        self.add_input('geometry:fuselage_width_max', val=np.nan)
        self.add_input('geometry:fuselage_height_max', val=np.nan)
        self.add_input('n1m1', val=np.nan)
        self.add_input('kfactors_a2:K_A2', val=1.)
        self.add_input('kfactors_a2:offset_A2', val=0.)
        self.add_input('kfactors_a2:K_tr', val=1.)
        self.add_input('kfactors_a2:K_fus', val=1.)

        self.add_output('weight_airframe:A2')

    def compute(self, inputs, outputs):
        S_mbf = inputs['geometry:fuselage_wet_area']
        width_max = inputs['geometry:fuselage_width_max']
        height_max = inputs['geometry:fuselage_height_max']
        n1m1 = inputs['n1m1']
        K_A2 = inputs['kfactors_a2:K_A2']
        offset_A2 = inputs['kfactors_a2:offset_A2']
        K_tr = inputs['kfactors_a2:K_tr']
        K_fus = inputs['kfactors_a2:K_fus']
        temp_A2 = S_mbf * (10 + 1.2 * sqrt(
            width_max * height_max) + 0.00019 * n1m1 / height_max ** 1.7) * K_tr * K_fus

        A2 = K_A2 * temp_A2 + offset_A2

        outputs['weight_airframe:A2'] = A2
