"""
Estimation of pylons weight
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


class PylonsWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Pylons weight estimation (A6) """

    def initialize(self):
        self.options.declare('engine_location', types=float, default=1.0)

    def setup(self):
        self.add_input('geometry:pylon_wet_area', val=np.nan, units="m**2")
        self.add_input('weight_propulsion:B1', val=np.nan, units="kg")
        self.add_input('geometry:engine_number', val=np.nan)
        self.add_input('kfactors_a6:K_A6', val=1.)
        self.add_input('kfactors_a6:offset_A6', val=0., units="kg")

        self.add_output('weight_airframe:A6', units="kg")

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        wet_area_pylon = inputs['geometry:pylon_wet_area']
        weight_engine = inputs['weight_propulsion:B1']
        n_engines = inputs['geometry:engine_number']
        k_a6 = inputs['kfactors_a6:K_A6']
        offset_a6 = inputs['kfactors_a6:offset_A6']

        if self.options['engine_location'] == 1.0:
            temp_a6 = 1.2 * wet_area_pylon ** 0.5 * (23 + 0.588 * (
                    weight_engine / n_engines) ** 0.708) * n_engines
        else:
            temp_a6 = 0.08 * weight_engine

        outputs['weight_airframe:A6'] = k_a6 * temp_a6 + offset_a6
