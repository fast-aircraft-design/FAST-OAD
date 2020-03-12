"""
Estimation of transmissions systems weight
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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

from fastoad.models.options import AIRCRAFT_TYPE_OPTION


class TransmissionSystemsWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Transmissions systems weight estimation (C4) """

    def initialize(self):
        self.options.declare(AIRCRAFT_TYPE_OPTION, types=float, default=2.0)

    def setup(self):
        self.add_input('tuning:weight:systems:transmission:mass:k', val=1.)
        self.add_input('tuning:weight:systems:transmission:mass:offset', val=0., units='kg')

        self.add_output('data:weight:systems:transmission:mass', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        k_c4 = inputs['tuning:weight:systems:transmission:mass:k']
        offset_c4 = inputs['tuning:weight:systems:transmission:mass:offset']

        aircraft_type = self.options[AIRCRAFT_TYPE_OPTION]
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

        outputs['data:weight:systems:transmission:mass'] = k_c4 * temp_c4 + offset_c4
