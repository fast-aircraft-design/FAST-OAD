"""
Estimation of life support systems weight
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


class LifeSupportSystemsWeight(ExplicitComponent):
    """ Life support systems weight estimation (C2) """

    def initialize(self):
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
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

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        width_max = inputs['geometry:fuselage_width_max']
        height_max = inputs['geometry:fuselage_height_max']
        cabin_length = inputs['geometry:fuselage_Lcabin']
        sweep_leading_edge = inputs['geometry:wing_sweep_0']
        n_engines = inputs['geometry:engine_number']
        span = inputs['geometry:wing_span']
        nacelle_diameter = inputs['geometry:nacelle_dia']
        npax1 = inputs['cabin:NPAX1']
        weight_engines = inputs['weight_propulsion:B1']
        cabin_crew = inputs['cabin:PNC']
        cockpit_crew = inputs['cabin:PNT']
        k_c21 = inputs['kfactors_c2:K_C21']
        offset_c21 = inputs['kfactors_c2:offset_C21']
        k_c22 = inputs['kfactors_c2:K_C22']
        offset_c22 = inputs['kfactors_c2:offset_C22']
        k_c23 = inputs['kfactors_c2:K_C23']
        offset_c23 = inputs['kfactors_c2:offset_C23']
        k_c24 = inputs['kfactors_c2:K_C24']
        offset_c24 = inputs['kfactors_c2:offset_C24']
        k_c25 = inputs['kfactors_c2:K_C25']
        offset_c25 = inputs['kfactors_c2:offset_C25']
        k_c26 = inputs['kfactors_c2:K_C26']
        offset_c26 = inputs['kfactors_c2:offset_C26']
        k_c27 = inputs['kfactors_c2:K_C27']
        offset_c27 = inputs['kfactors_c2:offset_C27']

        fuselage_diameter = np.sqrt(width_max * height_max)

        # Mass of insulating system
        temp_c21 = 9.3 * fuselage_diameter * cabin_length
        outputs['weight_systems:C21'] = k_c21 * temp_c21 + offset_c21

        # Mass of air conditioning and pressurization system
        if self.options['ac_type'] <= 3.0:
            temp_c22 = 200 + 27 * npax1 ** 0.46 + 7.2 * (n_engines ** 0.7) * (
                    npax1 ** 0.64) + npax1 + 0.0029 * npax1 ** 1.64
        else:
            temp_c22 = 450 + 51 * npax1 ** 0.46 + 7.2 * (n_engines ** 0.7) * (
                    npax1 ** 0.64) + npax1 + 0.0029 * npax1 ** 1.64
        outputs['weight_systems:C22'] = k_c22 * temp_c22 + offset_c22

        # Mass of de-icing system
        temp_c23 = 53 + 9.5 * nacelle_diameter * n_engines + 1.9 * (
                span - width_max) / np.cos(np.radians(sweep_leading_edge))
        outputs['weight_systems:C23'] = k_c23 * temp_c23 + offset_c23

        # Mass of internal lighting system
        temp_c24 = 1.4 * cabin_length * fuselage_diameter
        outputs['weight_systems:C24'] = k_c24 * temp_c24 + offset_c24

        # Mass of seats and installation system
        temp_c25 = 27 * cockpit_crew + 18 * cabin_crew
        outputs['weight_systems:C25'] = k_c25 * temp_c25 + offset_c25

        # Mass of fixed oxygen
        temp_c26 = 80 + 1.3 * npax1
        outputs['weight_systems:C26'] = k_c26 * temp_c26 + offset_c26

        # Mass of permanent security kits
        temp_c27 = 0.01 * weight_engines + 2.30 * npax1
        outputs['weight_systems:C27'] = k_c27 * temp_c27 + offset_c27
