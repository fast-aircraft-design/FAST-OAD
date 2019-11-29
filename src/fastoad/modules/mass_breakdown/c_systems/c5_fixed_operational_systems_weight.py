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
    # TODO: Document equations. Cite sources
    """ Fixed operational systems weight estimation (C5) """

    def setup(self):
        self.add_input('geometry:fuselage:rear_length', val=np.nan, units='m')
        self.add_input('geometry:fuselage:front_length', val=np.nan, units='m')
        self.add_input('geometry:fuselage:length', val=np.nan, units='m')
        self.add_input('geometry:cabin:seats:economical:count_by_row', val=np.nan)
        self.add_input('geometry:wing:root:chord', val=np.nan, units='m')
        self.add_input('geometry:cabin:containers:count_by_row', val=np.nan)
        self.add_input('weight:systems:operational:mass:k', val=1.)
        self.add_input('weight:systems:operational:mass:offset', val=0., units='kg')

        self.add_output('weight:systems:operational:radar:mass', units='kg')
        self.add_output('weight:systems:operational:cargo_hold:mass', units='kg')

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        front_section_length = inputs['geometry:fuselage:rear_length']
        aft_section_length = inputs['geometry:fuselage:front_length']
        fuselage_length = inputs['geometry:fuselage:length']
        front_seat_number_eco = inputs['geometry:cabin:seats:economical:count_by_row']
        l2_wing = inputs['geometry:wing:root:chord']
        side_by_side_container_number = inputs['geometry:cabin:containers:count_by_row']
        k_c5 = inputs['weight:systems:operational:mass:k']
        offset_c5 = inputs['weight:systems:operational:mass:offset']

        cylindrical_section_length = fuselage_length \
                                     - front_section_length \
                                     - aft_section_length

        cargo_compartment_length = cylindrical_section_length + 0.864 * (
                front_seat_number_eco - 5) - 0.8 * l2_wing

        # Radar
        temp_c51 = 100.
        outputs['weight:systems:operational:radar:mass'] = k_c5 * temp_c51 + offset_c5

        # Cargo container systems
        temp_c52 = 23.4 * cargo_compartment_length \
                   * side_by_side_container_number
        outputs['weight:systems:operational:cargo_hold:mass'] = k_c5 * temp_c52 + offset_c5
