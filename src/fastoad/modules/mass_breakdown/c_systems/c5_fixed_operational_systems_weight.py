"""
Estimation of fixed operational systems weight
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
    """ Fixed operational systems weight estimation (C5) """

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

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        front_section_length = inputs['geometry:fuselage_LAV']
        aft_section_length = inputs['geometry:fuselage_LAR']
        fuselage_length = inputs['geometry:fuselage_length']
        front_seat_number_eco = inputs['cabin:front_seat_number_eco']
        l2_wing = inputs['geometry:wing_l2']
        side_by_side_container_number = inputs['cabin:container_number_front']
        k_c5 = inputs['kfactors_c5:K_C5']
        offset_c5 = inputs['kfactors_c5:offset_C5']

        cylindrical_section_length = fuselage_length \
                                     - front_section_length \
                                     - aft_section_length

        cargo_compartment_length = cylindrical_section_length + 0.864 * (
                front_seat_number_eco - 5) - 0.8 * l2_wing

        # Radar
        temp_c51 = 100.
        outputs['weight_systems:C51'] = k_c5 * temp_c51 + offset_c5

        # Cargo container systems
        temp_c52 = 23.4 * cargo_compartment_length \
                   * side_by_side_container_number
        outputs['weight_systems:C52'] = k_c5 * temp_c52 + offset_c5
