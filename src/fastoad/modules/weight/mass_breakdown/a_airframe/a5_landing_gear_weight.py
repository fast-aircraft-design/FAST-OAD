"""
Estimation of landing gear weight
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


class LandingGearWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Landing gear weight estimation (A5) """

    def setup(self):
        self.add_input('weight:aircraft:MTOW', val=np.nan, units='kg')
        self.add_input('weight:airframe:landing_gear:mass:k', val=1.)
        self.add_input('weight:airframe:landing_gear:mass:offset', val=0., units='kg')

        self.add_output('weight:airframe:landing_gear:main:mass', units='kg')
        self.add_output('weight:airframe:landing_gear:front:mass', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        mtow = inputs['weight:aircraft:MTOW']
        k_a5 = inputs['weight:airframe:landing_gear:mass:k']
        offset_a5 = inputs['weight:airframe:landing_gear:mass:offset']

        temp_a51 = 18.1 + 0.131 * mtow ** 0.75 + 0.019 * mtow + 2.23E-5 * mtow ** 1.5
        temp_a52 = 9.1 + 0.082 * mtow ** 0.75 + 2.97E-6 * mtow ** 1.5

        a51 = k_a5 * temp_a51 + offset_a5
        a52 = k_a5 * temp_a52 + offset_a5

        outputs['weight:airframe:landing_gear:main:mass'] = a51
        outputs['weight:airframe:landing_gear:front:mass'] = a52
