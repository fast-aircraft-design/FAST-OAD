"""
    FAST - Copyright (c) 2016 ONERA ISAE
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

import math

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class Cd0HorizontalTail(ExplicitComponent):

    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        self.add_input('data:geometry:horizontal_tail:MAC:length', val=np.nan, units='m')
        self.add_input('data:geometry:horizontal_tail:thickness_ratio', val=np.nan)
        self.add_input('data:geometry:horizontal_tail:sweep_25', val=np.nan, units='deg')
        self.add_input('data:geometry:horizontal_tail:wetted_area', val=np.nan, units='m**2')
        self.add_input('data:geometry:wing:area', val=np.nan, units='m**2')
        if self.low_speed_aero:
            self.add_input('reynolds_low_speed', val=np.nan)
            self.add_input('Mach_low_speed', val=np.nan)
            self.add_output('cd0_ht_low_speed')
        else:
            self.add_input('data:aerodynamics:wing:cruise:reynolds', val=np.nan)
            self.add_input('data:TLAR:cruise_mach', val=np.nan)
            self.add_output('data:aerodynamics:horizontal_tail:cruise:CD0')

        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        el_ht = inputs['data:geometry:horizontal_tail:thickness_ratio']
        ht_length = inputs['data:geometry:horizontal_tail:MAC:length']
        sweep_25_ht = inputs['data:geometry:horizontal_tail:sweep_25']
        wet_area_ht = inputs['data:geometry:horizontal_tail:wetted_area']
        wing_area = inputs['data:geometry:wing:area']
        if self.low_speed_aero:
            mach = inputs['Mach_low_speed']
            re_hs = inputs['reynolds_low_speed']
        else:
            mach = inputs['data:TLAR:cruise_mach']
            re_hs = inputs['data:aerodynamics:wing:cruise:reynolds']

        ki_arrow_cd0 = 0.04

        cf_ht_hs = 0.455 / (
                (1 + 0.144 * mach ** 2) ** 0.65 * (math.log10(re_hs * ht_length)) ** 2.58)
        ke_cd0_ht = 4.688 * el_ht ** 2 + 3.146 * el_ht
        k_phi_cd0_ht = 1 - 0.000178 * sweep_25_ht ** 2 - 0.0065 * sweep_25_ht
        cd0_ht_hs = (ke_cd0_ht * k_phi_cd0_ht + ki_arrow_cd0 / 4 + 1
                     ) * cf_ht_hs * wet_area_ht / wing_area

        if self.low_speed_aero:
            outputs['cd0_ht_low_speed'] = cd0_ht_hs
        else:
            outputs['data:aerodynamics:horizontal_tail:cruise:CD0'] = cd0_ht_hs
