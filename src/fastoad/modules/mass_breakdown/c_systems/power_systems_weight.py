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


class PowerSystemsWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                                C1 - Power Systems
    # ----------------------------------------------------------------
    def setup(self):
        self.add_input('cabin:NPAX1', val=np.nan)
        self.add_input('weight_airframe:A4', val=np.nan)
        self.add_input('weight:MTOW', val=np.nan)
        self.add_input('kfactors_c1:K_C11', val=1.)
        self.add_input('kfactors_c1:offset_C11', val=0.)
        self.add_input('kfactors_c1:K_C12', val=1.)
        self.add_input('kfactors_c1:offset_C12', val=0.)
        self.add_input('kfactors_c1:K_C13', val=1.)
        self.add_input('kfactors_c1:offset_C13', val=0.)
        self.add_input('kfactors_c1:K_elec', val=1.)

        self.add_output('weight_systems:C11')
        self.add_output('weight_systems:C12')
        self.add_output('weight_systems:C13')

    def compute(self, inputs, outputs):
        NPAX1 = inputs['cabin:NPAX1']
        A4 = inputs['weight_airframe:A4']
        MTOW = inputs['weight:MTOW']
        K_C11 = inputs['kfactors_c1:K_C11']
        offset_C11 = inputs['kfactors_c1:offset_C11']
        K_C12 = inputs['kfactors_c1:K_C12']
        offset_C12 = inputs['kfactors_c1:offset_C12']
        K_C13 = inputs['kfactors_c1:K_C13']
        offset_C13 = inputs['kfactors_c1:offset_C13']
        K_elec = inputs['kfactors_c1:K_elec']

        # Mass of auxiliairy power unit
        temp_C11 = 11.3 * NPAX1 ** 0.64
        C11 = K_C11 * temp_C11 + offset_C11

        # Mass of electric system
        temp_C12 = K_elec * (0.444 * MTOW ** 0.66 + 2.54 * NPAX1 + 0.254 * A4)
        C12 = K_C12 * temp_C12 + offset_C12

        # Mass of the hydraulic system
        temp_C13 = K_elec * (0.256 * MTOW ** 0.66 + 1.46 * NPAX1 + 0.146 * A4)
        C13 = K_C13 * temp_C13 + offset_C13

        outputs['weight_systems:C11'] = C11
        outputs['weight_systems:C12'] = C12
        outputs['weight_systems:C13'] = C13
