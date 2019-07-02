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
from openmdao.core.explicitcomponent import ExplicitComponent


class CdCompressibility(ExplicitComponent):
    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        if self.low_speed_aero:
            self.add_input('Mach_low_speed', val=0.4)
            self.add_input('cl_low_speed', shape=(150))
            self.add_output('cd_comp_low_speed', shape=(150))
        else:
            self.add_input('tlar:cruise_Mach', val=0.4)
            self.add_input('cl_high_speed', shape=(150))
            self.add_output('cd_comp_high_speed', shape=(150))

    def compute(self, inputs, outputs):
        if self.low_speed_aero:
            cl = inputs['cl_low_speed']
            m = inputs['Mach_low_speed']
        else:
            cl = inputs['cl_high_speed']
            m = inputs['tlar:cruise_Mach']

        cd_comp = []

        for cl_val in cl:
            m_charac_comp = - 0.5 * cl_val ** 2 + 0.35 * \
                            cl_val + 0.765  # phi = 28deg, el_aero = 0.12, cl >= 0.35
            cd_comp.append(0.002 * exp(42.58 * (m - m_charac_comp)))

        if self.low_speed_aero:
            outputs['cd_comp_low_speed'] = cd_comp
        else:
            outputs['cd_comp_high_speed'] = cd_comp
