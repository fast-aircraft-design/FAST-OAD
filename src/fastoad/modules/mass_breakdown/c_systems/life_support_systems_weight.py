"""
    FAST - Copyright (c) 2016 ONERA ISAE
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
from math import sqrt, pi, cos
from openmdao.core.explicitcomponent import ExplicitComponent


class LifeSupportSystemsWeight(ExplicitComponent):
    # ----------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                                C2 - Life Support Systems
    # ----------------------------------------------------------------
    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.ac_type = self.options['ac_type']

        self.add_input('geometry:fuselage_width_max', val=np.nan)
        self.add_input('geometry:fuselage_height_max', val=np.nan)
        self.add_input('geometry:fuselage_Lcabin', val=np.nan)
        self.add_input('geometry:wing_sweep_0', val=np.nan)
        self.add_input('geometry:nacelle_dia', val=np.nan)
        self.add_input('geometry:engine_number', val=np.nan)
        self.add_input('cabin:NPAX1', val=np.nan)
        self.add_input('cabin:PNT', val=np.nan)
        self.add_input('cabin:PNC', val=np.nan)
        self.add_input('geometry:wing_span', val=np.nan)
        self.add_input('weight_propulsion:B1', val=np.nan)
        self.add_input('kfactors_c2:K_C21', val=1.)
        self.add_input('kfactors_c2:offset_C21', val=0.)
        self.add_input('kfactors_c2:K_C22', val=1.)
        self.add_input('kfactors_c2:offset_C22', val=0.)
        self.add_input('kfactors_c2:K_C23', val=1.)
        self.add_input('kfactors_c2:offset_C23', val=0.)
        self.add_input('kfactors_c2:K_C24', val=1.)
        self.add_input('kfactors_c2:offset_C24', val=0.)
        self.add_input('kfactors_c2:K_C25', val=1.)
        self.add_input('kfactors_c2:offset_C25', val=0.)
        self.add_input('kfactors_c2:K_C26', val=1.)
        self.add_input('kfactors_c2:offset_C26', val=0.)
        self.add_input('kfactors_c2:K_C27', val=1.)
        self.add_input('kfactors_c2:offset_C27', val=0.)

        self.add_output('weight_systems:C21')
        self.add_output('weight_systems:C22')
        self.add_output('weight_systems:C23')
        self.add_output('weight_systems:C24')
        self.add_output('weight_systems:C25')
        self.add_output('weight_systems:C26')
        self.add_output('weight_systems:C27')

    def compute(self, inputs, outputs):
        width_max = inputs['geometry:fuselage_width_max']
        height_max = inputs['geometry:fuselage_height_max']
        cabin_length = inputs['geometry:fuselage_Lcabin']
        sweep_LE = inputs['geometry:wing_sweep_0']
        n_engines = inputs['geometry:engine_number']
        span = inputs['geometry:wing_span']
        nacelle_dia = inputs['geometry:nacelle_dia']
        NPAX1 = inputs['cabin:NPAX1']
        weight_engines = inputs['weight_propulsion:B1']
        PNC = inputs['cabin:PNC']
        PNT = inputs['cabin:PNT']
        K_C21 = inputs['kfactors_c2:K_C21']
        offset_C21 = inputs['kfactors_c2:offset_C21']
        K_C22 = inputs['kfactors_c2:K_C22']
        offset_C22 = inputs['kfactors_c2:offset_C22']
        K_C23 = inputs['kfactors_c2:K_C23']
        offset_C23 = inputs['kfactors_c2:offset_C23']
        K_C24 = inputs['kfactors_c2:K_C24']
        offset_C24 = inputs['kfactors_c2:offset_C24']
        K_C25 = inputs['kfactors_c2:K_C25']
        offset_C25 = inputs['kfactors_c2:offset_C25']
        K_C26 = inputs['kfactors_c2:K_C26']
        offset_C26 = inputs['kfactors_c2:offset_C26']
        K_C27 = inputs['kfactors_c2:K_C27']
        offset_C27 = inputs['kfactors_c2:offset_C27']

        fus_diam = sqrt(width_max * height_max)

        # Mass of insulating system
        temp_C21 = 9.3 * fus_diam * cabin_length
        C21 = K_C21 * temp_C21 + offset_C21

        # Mass of air conditioning and pressurization system
        if self.ac_type <= 3.0:
            temp_C22 = 200 + 27 * NPAX1 ** 0.46 + 7.2 * (n_engines ** 0.7) * (
                    NPAX1 ** 0.64) + NPAX1 + 0.0029 * NPAX1 ** 1.64
        else:
            temp_C22 = 450 + 51 * NPAX1 ** 0.46 + 7.2 * (n_engines ** 0.7) * (
                    NPAX1 ** 0.64) + NPAX1 + 0.0029 * NPAX1 ** 1.64
        C22 = K_C22 * temp_C22 + offset_C22

        # Mass of de-icing system
        temp_C23 = 53 + 9.5 * nacelle_dia * n_engines + 1.9 * (span - width_max) / cos(
            (sweep_LE / 180. * pi))
        C23 = K_C23 * temp_C23 + offset_C23

        # Mass of internal lighting system
        temp_C24 = 1.4 * cabin_length * fus_diam
        C24 = K_C24 * temp_C24 + offset_C24

        # Mass of seats and installation system
        temp_C25 = 27 * PNT + 18 * PNC
        C25 = K_C25 * temp_C25 + offset_C25

        # Mass of fixed oxygen
        temp_C26 = 80 + 1.3 * NPAX1
        C26 = K_C26 * temp_C26 + offset_C26

        # Mass of permanent security kits
        temp_C27 = 0.01 * weight_engines + 2.30 * NPAX1
        C27 = K_C27 * temp_C27 + offset_C27

        outputs['weight_systems:C21'] = C21
        outputs['weight_systems:C22'] = C22
        outputs['weight_systems:C23'] = C23
        outputs['weight_systems:C24'] = C24
        outputs['weight_systems:C25'] = C25
        outputs['weight_systems:C26'] = C26
        outputs['weight_systems:C27'] = C27
