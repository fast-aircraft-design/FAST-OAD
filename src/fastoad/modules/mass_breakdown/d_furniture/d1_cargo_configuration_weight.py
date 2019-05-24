"""
Estimation of cargo configuration weight
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


class CargoConfigurationWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Cargo configuration weight estimation (D1) """

    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.add_input('cabin:NPAX1', val=np.nan)
        self.add_input('cabin:container_number', val=np.nan)
        self.add_input('cabin:pallet_number', val=np.nan)
        self.add_input('cabin:front_seat_number_eco', val=np.nan)
        self.add_input('kfactors_d1:K_D1', val=1.)
        self.add_input('kfactors_d1:offset_D1', val=0., units='kg')

        self.add_output('weight_furniture:D1', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        npax1 = inputs['cabin:NPAX1']
        side_by_side_eco_seat_count = inputs['cabin:front_seat_number_eco']
        container_count = inputs['cabin:container_number']
        pallet_number = inputs['cabin:pallet_number']
        k_d1 = inputs['kfactors_d1:K_D1']
        offset_d1 = inputs['kfactors_d1:offset_D1']

        if self.options['ac_type'] == 6.0:
            if side_by_side_eco_seat_count <= 6.0:
                temp_d1 = 0.351 * (npax1 - 38)
            else:
                temp_d1 = 85 * container_count + 110 * pallet_number
            outputs['weight_furniture:D1'] = k_d1 * temp_d1 + offset_d1
        else:
            outputs['weight_furniture:D1'] = 0.
