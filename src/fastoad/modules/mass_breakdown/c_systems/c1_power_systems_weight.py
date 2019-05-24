"""
Estimation of power systems weight
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


class PowerSystemsWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Power systems weight estimation (C1) """
    def setup(self):
        self.add_input('cabin:NPAX1', val=np.nan)
        self.add_input('weight_airframe:A4', val=np.nan, units='kg')
        self.add_input('weight:MTOW', val=np.nan, units='kg')
        self.add_input('kfactors_c1:K_C11', val=1.)
        self.add_input('kfactors_c1:offset_C11', val=0., units='kg')
        self.add_input('kfactors_c1:K_C12', val=1.)
        self.add_input('kfactors_c1:offset_C12', val=0., units='kg')
        self.add_input('kfactors_c1:K_C13', val=1.)
        self.add_input('kfactors_c1:offset_C13', val=0., units='kg')
        self.add_input('kfactors_c1:K_elec', val=1.)

        self.add_output('weight_systems:C11', units='kg')
        self.add_output('weight_systems:C12', units='kg')
        self.add_output('weight_systems:C13', units='kg')

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        npax1 = inputs['cabin:NPAX1']
        flight_controls_weight = inputs['weight_airframe:A4']
        mtow = inputs['weight:MTOW']
        k_c11 = inputs['kfactors_c1:K_C11']
        offset_c11 = inputs['kfactors_c1:offset_C11']
        k_c12 = inputs['kfactors_c1:K_C12']
        offset_c12 = inputs['kfactors_c1:offset_C12']
        k_c13 = inputs['kfactors_c1:K_C13']
        offset_c13 = inputs['kfactors_c1:offset_C13']
        k_elec = inputs['kfactors_c1:K_elec']

        # Mass of auxiliary power unit
        temp_c11 = 11.3 * npax1 ** 0.64
        outputs['weight_systems:C11'] = k_c11 * temp_c11 + offset_c11

        # Mass of electric system
        temp_c12 = k_elec * (
                0.444 * mtow ** 0.66
                + 2.54 * npax1 + 0.254 * flight_controls_weight)
        outputs['weight_systems:C12'] = k_c12 * temp_c12 + offset_c12

        # Mass of the hydraulic system
        temp_c13 = k_elec * (
                0.256 * mtow ** 0.66 + 1.46 * npax1
                + 0.146 * flight_controls_weight)
        outputs['weight_systems:C13'] = k_c13 * temp_c13 + offset_c13
