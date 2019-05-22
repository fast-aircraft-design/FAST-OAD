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


class PassengerSeatsWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                     D2 - Passenger Seats
    # ----------------------------------------------------------------
    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.ac_type = self.options['ac_type']

        self.add_input('tlar:NPAX', val=np.nan)
        self.add_input('kfactors_d2:K_D2', val=1.)
        self.add_input('kfactors_d2:offset_D2', val=0.)

        self.add_output('weight_furniture:D2')

    def compute(self, inputs, outputs):
        NPAX = inputs['tlar:NPAX']
        K_D2 = inputs['kfactors_d2:K_D2']
        offset_D2 = inputs['kfactors_d2:offset_D2']

        if self.ac_type == 1.0:
            K_PS = 9.0
        if (self.ac_type == 2.0) or (self.ac_type == 3.0):
            K_PS = 10.0
        if (self.ac_type == 4.0) or (self.ac_type == 5.0):
            K_PS = 11.0
        if self.ac_type == 6.0:
            K_PS = 0.

        temp_D2 = K_PS * NPAX
        D2 = K_D2 * temp_D2 + offset_D2

        outputs['weight_furniture:D2'] = D2
