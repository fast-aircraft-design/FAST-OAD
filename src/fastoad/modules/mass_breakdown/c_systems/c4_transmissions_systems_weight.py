"""
Estimation of transmissions systems weight
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
from openmdao.core.explicitcomponent import ExplicitComponent


class TransmissionSystemsWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Transmissions systems weight estimation (C4) """

    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.add_input('kfactors_c4:K_C4', val=1.)
        self.add_input('kfactors_c4:offset_C4', val=0., units='kg')

        self.add_output('weight_systems:C4', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        k_c4 = inputs['kfactors_c4:K_C4']
        offset_c4 = inputs['kfactors_c4:offset_C4']

        aircraft_type = self.options['ac_type']
        if aircraft_type == 1.0:
            temp_c4 = 100.0
        elif aircraft_type == 2.0:
            temp_c4 = 200.0
        elif aircraft_type == 3.0:
            temp_c4 = 250.0
        elif aircraft_type in [4.0, 5.0]:
            temp_c4 = 350.0
        else:
            raise ValueError("Unexpected aircraft type")

        outputs['weight_systems:C4'] = k_c4 * temp_c4 + offset_c4
