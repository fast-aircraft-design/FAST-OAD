"""
Estimation of fuselage weight
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


class FuselageWeight(ExplicitComponent):
    """ Fuselage weight estimation (A2) """

    def setup(self):
        self.add_input('geometry:fuselage_wet_area', val=np.nan, units="m**2")
        self.add_input('geometry:fuselage_width_max', val=np.nan, units="m")
        self.add_input('geometry:fuselage_height_max', val=np.nan, units="m")
        self.add_input('n1m1', val=np.nan, units="kg")
        self.add_input('kfactors_a2:K_A2', val=1.)
        self.add_input('kfactors_a2:offset_A2', val=0., units="kg")
        self.add_input('kfactors_a2:K_tr', val=1.)
        self.add_input('kfactors_a2:K_fus', val=1.)

        self.add_output('weight_airframe:A2', units="kg")

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        fuselage_wet_area = inputs['geometry:fuselage_wet_area']
        width_max = inputs['geometry:fuselage_width_max']
        height_max = inputs['geometry:fuselage_height_max']
        n1m1 = inputs['n1m1']
        k_a2 = inputs['kfactors_a2:K_A2']
        offset_a2 = inputs['kfactors_a2:offset_A2']
        k_lg = inputs['kfactors_a2:K_tr']
        k_fus = inputs['kfactors_a2:K_fus']

        temp_a2 = fuselage_wet_area * (10 + 1.2 * np.sqrt(
            width_max * height_max) + 0.00019 * n1m1 / height_max ** 1.7
                                       ) * k_lg * k_fus
        outputs['weight_airframe:A2'] = k_a2 * temp_a2 + offset_a2
