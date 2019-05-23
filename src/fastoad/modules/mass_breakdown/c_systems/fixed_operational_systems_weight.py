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


class FixedOperationalSystemsWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                     C5 - Fixed Operational Systems
    # ----------------------------------------------------------------
    def setup(self):
        self.add_input('geometry:fuselage_LAV', val=np.nan)
        self.add_input('geometry:fuselage_LAR', val=np.nan)
        self.add_input('geometry:fuselage_length', val=np.nan)
        self.add_input('cabin:front_seat_number_eco', val=np.nan)
        self.add_input('geometry:wing_l2', val=np.nan)
        self.add_input('cabin:container_number_front', val=np.nan)
        self.add_input('kfactors_c5:K_C5', val=1.)
        self.add_input('kfactors_c5:offset_C5', val=0.)

        self.add_output('weight_systems:C51')
        self.add_output('weight_systems:C52')

    def compute(self, inputs, outputs):
        LAV = inputs['geometry:fuselage_LAV']
        LAR = inputs['geometry:fuselage_LAR']
        fus_length = inputs['geometry:fuselage_length']
        front_seat_number_eco = inputs['cabin:front_seat_number_eco']
        l2_wing = inputs['geometry:wing_l2']
        container_number_front = inputs['cabin:container_number_front']
        K_C5 = inputs['kfactors_c5:K_C5']
        offset_C5 = inputs['kfactors_c5:offset_C5']

        L_cyl = fus_length - LAV - LAR

        L_cargo = L_cyl + 0.864 * (front_seat_number_eco - 5) - 0.8 * l2_wing

        temp_C51 = 100.
        temp_C52 = 23.4 * L_cargo * container_number_front

        C51 = K_C5 * temp_C51 + offset_C5
        C52 = K_C5 * temp_C52 + offset_C5

        outputs['weight_systems:C51'] = C51
        outputs['weight_systems:C52'] = C52
