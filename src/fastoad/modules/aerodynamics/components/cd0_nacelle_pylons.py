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

import math
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent

from fastoad.modules.aerodynamics.constants import POLAR_POINT_COUNT


class Cd0NacelleAndPylons(ExplicitComponent):
    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        nans_array = np.full(POLAR_POINT_COUNT, np.nan)
        if self.low_speed_aero:
            self.add_input('reynolds_low_speed', val=np.nan)
            self.add_input('Mach_low_speed', val=np.nan)
            self.add_output('cd0_nacelle_low_speed', val=np.nan)
            self.add_output('cd0_pylon_low_speed', val=np.nan)
        else:
            self.add_input('reynolds_high_speed', val=np.nan)
            self.add_input('cl_high_speed', val=nans_array)
            self.add_input('tlar:cruise_Mach', val=np.nan)
            self.add_output('cd0_nacelle_high_speed', val=np.nan)
            self.add_output('cd0_pylon_high_speed', val=np.nan)

        self.add_input('geometry:pylon_length', val=np.nan, units='m')
        self.add_input('geometry:nacelle_length', val=np.nan, units='m')
        self.add_input('geometry:pylon_wet_area', val=np.nan, units='m**2')
        self.add_input('geometry:nacelle_wet_area', val=np.nan, units='m**2')
        self.add_input('geometry:engine_number', val=np.nan)
        self.add_input('geometry:fan_length', val=np.nan, units='m')
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')

    def compute(self, inputs, outputs):
        pylon_length = inputs['geometry:pylon_length']
        nac_length = inputs['geometry:nacelle_length']
        wet_area_pylon = inputs['geometry:pylon_wet_area']
        wet_area_nac = inputs['geometry:nacelle_wet_area']
        n_engines = inputs['geometry:engine_number']
        fan_length = inputs['geometry:fan_length']
        wing_area = inputs['geometry:wing_area']
        if self.low_speed_aero:
            mach = inputs['Mach_low_speed']
            re_hs = inputs['reynolds_low_speed']
        else:
            mach = inputs['tlar:cruise_Mach']
            re_hs = inputs['reynolds_high_speed']

        cf_pylon_hs = 0.455 / (
                (1 + 0.126 * mach ** 2) * (math.log10(re_hs * pylon_length)) ** (2.58))
        cf_nac_hs = 0.455 / ((1 + 0.126 * mach ** 2) * (math.log10(re_hs * nac_length)) ** (2.58))

        # cd0 Pylon
        el_pylon = 0.06
        ke_cd0_pylon = 4.688 * el_pylon ** 2 + 3.146 * el_pylon
        cd0_pylon_hs = n_engines * (1 + ke_cd0_pylon) * cf_pylon_hs * wet_area_pylon / wing_area

        # cd0 Nacelles
        e_fan = 0.22
        kn_cd0_nac = 1 + 0.05 + 5.8 * e_fan / fan_length
        cd0_int_nac = 0.0002
        cd0_nac_hs = n_engines * (kn_cd0_nac * cf_nac_hs * wet_area_nac / wing_area + cd0_int_nac)

        if self.low_speed_aero:
            outputs['cd0_pylon_low_speed'] = cd0_pylon_hs
            outputs['cd0_nacelle_low_speed'] = cd0_nac_hs
        else:
            outputs['cd0_pylon_high_speed'] = cd0_pylon_hs
            outputs['cd0_nacelle_high_speed'] = cd0_nac_hs
