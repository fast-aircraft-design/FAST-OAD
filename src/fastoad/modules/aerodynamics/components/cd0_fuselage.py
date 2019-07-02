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

from openmdao.core.explicitcomponent import ExplicitComponent


class Cd0Fuselage(ExplicitComponent):
    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        if self.low_speed_aero:
            self.add_input('reynolds_low_speed', val=1e3)
            self.add_input('cl_low_speed', shape=(150))
            self.add_input('Mach_low_speed', val=0.4)
            self.add_output('cd0_fuselage_low_speed', shape=(150))
        else:
            self.add_input('reynolds_high_speed', val=1e3)
            self.add_input('cl_high_speed', shape=(150))
            self.add_input('tlar:cruise_Mach', val=0.78)
            self.add_output('cd0_fuselage_high_speed', shape=(150))

        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:fuselage_length', val=33.)
        self.add_input('geometry:fuselage_width_max', val=4.)
        self.add_input('geometry:fuselage_height_max', val=4.)
        self.add_input('geometry:fuselage_wet_area', val=400.)

    def compute(self, inputs, outputs):
        height_max = inputs['geometry:fuselage_height_max']
        width_max = inputs['geometry:fuselage_width_max']
        wet_area_fus = inputs['geometry:fuselage_wet_area']
        wing_area = inputs['geometry:wing_area']
        fus_length = inputs['geometry:fuselage_length']
        if self.low_speed_aero:
            cl = inputs['cl_low_speed']
            mach = inputs['Mach_low_speed']
            re_hs = inputs['reynolds_low_speed']
        else:
            cl = inputs['cl_high_speed']
            mach = inputs['tlar:cruise_Mach']
            re_hs = inputs['reynolds_high_speed']

        cd0_fus = []
        cf_fus_hs = 0.455 / ((1 + 0.126 * mach ** 2) * (math.log10(re_hs * fus_length)) ** (2.58))

        cd0_friction_fus_hs = (0.98 + 0.745 * math.sqrt(height_max *
                                                        width_max) / fus_length) * \
                              cf_fus_hs * wet_area_fus / wing_area
        for cl_val in cl:
            cd0_upsweep_fus_hs = (
                                         0.0029 * cl_val ** 2 - 0.0066 * cl_val + 0.0043) * (
                                         0.67 * 3.6 * height_max * width_max) / wing_area
            cd0_fus.append(cd0_friction_fus_hs + cd0_upsweep_fus_hs)

        if self.low_speed_aero:
            outputs['cd0_fuselage_low_speed'] = cd0_fus
        else:
            outputs['cd0_fuselage_high_speed'] = cd0_fus


