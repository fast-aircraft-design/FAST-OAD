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


class PylonsWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                                A6 - Pylons
    # ---------------------------------------------------------------
    def initialize(self):
        self.options.declare('engine_location', types=float, default=1.0)

    def setup(self):
        self.engine_loc = self.options['engine_location']

        self.add_input('geometry:pylon_wet_area', val=np.nan)
        self.add_input('weight_propulsion:B1', val=np.nan)
        self.add_input('geometry:engine_number', val=np.nan)
        self.add_input('kfactors_a6:K_A6', val=1.)
        self.add_input('kfactors_a6:offset_A6', val=0.)

        self.add_output('weight_airframe:A6')

    def compute(self, inputs, outputs):
        wet_area_pylon = inputs['geometry:pylon_wet_area']
        weight_engine = inputs['weight_propulsion:B1']
        n_engines = inputs['geometry:engine_number']
        K_A6 = inputs['kfactors_a6:K_A6']
        offset_A6 = inputs['kfactors_a6:offset_A6']

        if self.engine_loc == 1.0:
            temp_A6 = 1.2 * wet_area_pylon ** 0.5 * (
                        23 + 0.588 * (weight_engine / n_engines) ** 0.708) * n_engines
        else:
            temp_A6 = 0.08 * weight_engine

        A6 = K_A6 * temp_A6 + offset_A6

        outputs['weight_airframe:A6'] = A6
