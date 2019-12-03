"""
Estimation of engine weight
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


class EngineWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Engine weight estimation (B1) """

    def setup(self):
        self.add_input('propulsion:MTO_thrust', val=np.nan, units='N')
        self.add_input('geometry:propulsion:engine:count', val=np.nan)
        self.add_input('weight:propulsion:engine:mass:k', val=1.)
        self.add_input('weight:propulsion:engine:mass:offset', val=0., units='kg')

        self.add_output('weight:propulsion:engine:mass', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        sea_level_thrust = inputs['propulsion:MTO_thrust']
        n_engines = inputs['geometry:propulsion:engine:count']
        k_b1 = inputs['weight:propulsion:engine:mass:k']
        offset_b1 = inputs['weight:propulsion:engine:mass:offset']

        if sea_level_thrust < 80000:
            temp_b1 = 22.2e-3 * sea_level_thrust
        else:
            temp_b1 = 14.1e-3 * sea_level_thrust + 648

        temp_b1 *= n_engines * 1.55
        outputs['weight:propulsion:engine:mass'] = k_b1 * temp_b1 + offset_b1
