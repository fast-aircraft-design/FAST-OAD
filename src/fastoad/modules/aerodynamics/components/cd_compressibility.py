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

from math import exp

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent

from fastoad.modules.aerodynamics.constants import POLAR_POINT_COUNT


class CdCompressibility(ExplicitComponent):
    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        nans_array = np.full(POLAR_POINT_COUNT, np.nan)
        if self.low_speed_aero:
            self.add_input('Mach_low_speed', val=np.nan)
            self.add_input('cl_low_speed', val=nans_array)
            self.add_output('cd_comp_low_speed', val=nans_array)
        else:
            self.add_input('tlar:cruise_Mach', val=np.nan)
            self.add_input('cl_high_speed', val=nans_array)
            self.add_output('cd_comp_high_speed', val=nans_array)

    def compute(self, inputs, outputs):
        if self.low_speed_aero:
            cl = inputs['cl_low_speed']
            m = inputs['Mach_low_speed']
        else:
            cl = inputs['cl_high_speed']
            m = inputs['tlar:cruise_Mach']

        cd_comp = []

        for cl_val in cl:
            # FIXME: The computed characteristic Mach is for sweep angle 28° and relative thickness
            #        of 0.12. It should be corrected according to actual values
            m_charac_comp = - 0.5 * max(0.35, cl_val) ** 2 + 0.35 * max(0.35, cl_val) + 0.765
            cd_comp.append(0.002 * exp(42.58 * (m - m_charac_comp)))

        if self.low_speed_aero:
            outputs['cd_comp_low_speed'] = cd_comp
        else:
            outputs['cd_comp_high_speed'] = cd_comp
