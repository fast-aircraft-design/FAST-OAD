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


class EmpennageWeight(ExplicitComponent):
    # --------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                                A3 - Empennage
    # ---------------------------------------------------------------
    def initialize(self):
        self.options.declare('engine_location', types=float, default=1.0)
        self.options.declare('tail_type', types=float, default=0.)

    def setup(self):
        self.engine_loc = self.options['engine_location']
        self.tail_type = self.options['tail_type']

        self.add_input('geometry:ht_area', val=np.nan)
        self.add_input('geometry:vt_area', val=np.nan)
        self.add_input('kfactors_a3:K_A31', val=1.)
        self.add_input('kfactors_a3:offset_A31', val=0.)
        self.add_input('kfactors_a3:K_A32', val=1.)
        self.add_input('kfactors_a3:offset_A32', val=0.)

        self.add_output('weight_airframe:A31')
        self.add_output('weight_airframe:A32')

    def compute(self, inputs, outputs):
        HT_area = inputs['geometry:ht_area']
        VT_area = inputs['geometry:vt_area']
        K_A31 = inputs['kfactors_a3:K_A31']
        offset_A31 = inputs['kfactors_a3:offset_A31']
        K_A32 = inputs['kfactors_a3:K_A32']
        offset_A32 = inputs['kfactors_a3:offset_A32']

        if self.tail_type == 1.:
            k_tail = 1.3
        else:
            k_tail = 1.
        # Mass of the horizontal tail plane
        temp_A31 = HT_area * (14.4 + 0.155 * HT_area) * k_tail
        A31 = K_A31 * temp_A31 + offset_A31

        # Mass of the vertical tail plane
        if self.engine_loc == 1:
            k_engine = 1.
        else:
            k_engine = 1.5

        temp_A32 = VT_area * (15.45 + 0.202 * VT_area) * k_engine * k_tail
        A32 = K_A32 * temp_A32 + offset_A32

        outputs['weight_airframe:A31'] = A31
        outputs['weight_airframe:A32'] = A32
