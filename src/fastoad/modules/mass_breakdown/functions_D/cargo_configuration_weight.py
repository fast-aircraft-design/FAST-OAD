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


class CargoConfigurationWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                     D1 - Cargo configuration
    # ----------------------------------------------------------------
    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.ac_type = self.options['ac_type']

        self.add_input('cabin:NPAX1', val=np.nan)
        self.add_input('cabin:container_number', val=np.nan)
        self.add_input('cabin:pallet_number', val=np.nan)
        self.add_input('cabin:front_seat_number_eco', val=np.nan)
        self.add_input('kfactors_d1:K_D1', val=1.)
        self.add_input('kfactors_d1:offset_D1', val=0.)

        self.add_output('weight_furniture:D1')

    def compute(self, inputs, outputs):
        NPAX1 = inputs['cabin:NPAX1']
        front_seat_number_eco = inputs['cabin:front_seat_number_eco']
        container_number = inputs['cabin:container_number']
        pallet_number = inputs['cabin:pallet_number']
        K_D1 = inputs['kfactors_d1:K_D1']
        offset_D1 = inputs['kfactors_d1:offset_D1']

        if self.ac_type == 6.0:
            if front_seat_number_eco <= 6.0:
                temp_D1 = 0.351 * (NPAX1 - 38)
            else:
                temp_D1 = 85 * container_number + 110 * pallet_number
            D1 = K_D1 * temp_D1 + offset_D1
        else:
            D1 = 0.

        outputs['weight_furniture:D1'] = D1
