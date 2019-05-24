"""
Estimation of flight controls weight
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


class FlightControlsWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Flight controls weight estimation (A4) """

    def setup(self):
        self.add_input('geometry:fuselage_length', val=np.nan, units="m")
        self.add_input('geometry:wing_b_50', val=np.nan, units="m")
        self.add_input('n1m1', val=np.nan, units="kg")
        self.add_input('n2m2', val=np.nan, units="kg")
        self.add_input('kfactors_a4:K_fc', val=1.)
        self.add_input('kfactors_a4:K_A4', val=1.)
        self.add_input('kfactors_a4:offset_A4', val=0., units="kg")

        self.add_output('weight_airframe:A4', units="kg")

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        fus_length = inputs['geometry:fuselage_length']
        b_50 = inputs['geometry:wing_b_50']
        k_fc = inputs['kfactors_a4:K_fc']
        k_a4 = inputs['kfactors_a4:K_A4']
        offset_a4 = inputs['kfactors_a4:offset_A4']

        max_nm = max(inputs['n1m1'], inputs['n2m2'])

        temp_a4 = k_fc * max_nm * (fus_length ** 0.66 + b_50 ** 0.66)

        outputs['weight_airframe:A4'] = k_a4 * temp_a4 + offset_a4
