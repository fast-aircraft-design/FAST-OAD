"""
Estimation of empennage weight
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


class EmpennageWeight(ExplicitComponent):
    """ Wing weight estimation (A3) """

    def initialize(self):
        self.options.declare('engine_location', types=float, default=1.0)
        self.options.declare('tail_type', types=float, default=0.)

    def setup(self):
        self.add_input('geometry:ht_area', val=np.nan, units="m**2")
        self.add_input('geometry:vt_area', val=np.nan, units="m**2")
        self.add_input('kfactors_a3:K_A31', val=1.)
        self.add_input('kfactors_a3:offset_A31', val=0., units="kg")
        self.add_input('kfactors_a3:K_A32', val=1.)
        self.add_input('kfactors_a3:offset_A32', val=0., units="kg")

        self.add_output('weight_airframe:A31', units="kg")
        self.add_output('weight_airframe:A32', units="kg")

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        ht_area = inputs['geometry:ht_area']
        vt_area = inputs['geometry:vt_area']
        k_a31 = inputs['kfactors_a3:K_A31']
        offset_a31 = inputs['kfactors_a3:offset_A31']
        k_a32 = inputs['kfactors_a3:K_A32']
        offset_a32 = inputs['kfactors_a3:offset_A32']

        k_tail = 1.3 if self.options['tail_type'] == 1 else 1.

        # Mass of the horizontal tail plane
        temp_a31 = ht_area * (14.4 + 0.155 * ht_area) * k_tail
        outputs['weight_airframe:A31'] = k_a31 * temp_a31 + offset_a31

        # Mass of the vertical tail plane
        k_engine = 1 if self.options['engine_location'] == 1. else 1.5

        temp_a32 = vt_area * (15.45 + 0.202 * vt_area) * k_engine * k_tail
        outputs['weight_airframe:A32'] = k_a32 * temp_a32 + offset_a32
