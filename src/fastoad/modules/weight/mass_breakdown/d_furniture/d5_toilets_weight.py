"""
Estimation of toilets weight
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
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent

from fastoad.modules.options import AIRCRAFT_TYPE_OPTION


class ToiletsWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Toilets kit weight estimation (D5) """

    def initialize(self):
        self.options.declare(AIRCRAFT_TYPE_OPTION, types=float, default=2.0)

    def setup(self):
        self.add_input('TLAR:NPAX', val=np.nan)
        self.add_input('weight:furniture:toilets:mass:k', val=1.)
        self.add_input('weight:furniture:toilets:mass:offset', val=0., units='kg')

        self.add_output('weight:furniture:toilets:mass', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        npax = inputs['TLAR:NPAX']
        k_d5 = inputs['weight:furniture:toilets:mass:k']
        offset_d5 = inputs['weight:furniture:toilets:mass:offset']

        aircraft_type = self.options[AIRCRAFT_TYPE_OPTION]
        if aircraft_type == 1.0:
            k_toilet = 0.1
        elif aircraft_type == 2.0:
            k_toilet = 0.5
        elif aircraft_type == 3.0:
            k_toilet = 1.0
        elif aircraft_type in (4.0, 5.0):
            k_toilet = 1.5
        elif aircraft_type == 6.0:
            k_toilet = 0.
        else:
            raise ValueError("Unexpected aircraft type")

        temp_d5 = k_toilet * npax
        outputs['weight:furniture:toilets:mass'] = k_d5 * temp_d5 + offset_d5
