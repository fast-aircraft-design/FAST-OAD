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


class Cd0Wing(ExplicitComponent):
    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        if self.low_speed_aero:
            self.add_input('reynolds_low_speed', val=1e3)
            self.add_input('cl_low_speed', shape=(150))
            self.add_input('Mach_low_speed', val=0.1)
            self.add_output('cd0_wing_low_speed', shape=(150))
        else:
            self.add_input('reynolds_high_speed', val=1e3)
            self.add_input('cl_high_speed', shape=(150))
            self.add_input('tlar:cruise_Mach', val=0.78)
            self.add_output('cd0_wing_high_speed', shape=(150))

        self.add_input('geometry:wing_area', val=124.)
        self.add_input('geometry:wing_toc_aero', val=0.128)
        self.add_input('geometry:wing_wet_area', val=200.)
        self.add_input('geometry:wing_l0', val=4.2)
        self.add_input('geometry:wing_sweep_25', val=25)

    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        wet_area_wing = inputs['geometry:wing_wet_area']
        el_aero = inputs['geometry:wing_toc_aero']
        sweep_25 = inputs['geometry:wing_sweep_25']
        l0_wing = inputs['geometry:wing_l0']
        if self.low_speed_aero:
            cl = inputs['cl_low_speed']
            mach = inputs['Mach_low_speed']
            re_hs = inputs['reynolds_low_speed']
        else:
            cl = inputs['cl_high_speed']
            mach = inputs['tlar:cruise_Mach']
            re_hs = inputs['reynolds_high_speed']

        cd0 = []
        ki_arrow_cd0 = 0.04
        # Friction coefficients
        cf_wing_hs = 0.455 / ((1 + 0.126 * mach ** 2) * (math.log10(re_hs * l0_wing)) ** (2.58))

        # cd0 wing
        # factor of relative thickness
        ke_cd0_wing = 4.688 * el_aero ** 2 + 3.146 * el_aero
        k_phi_cd0_wing = 1 - 0.000178 * \
                         (sweep_25) ** 2 - 0.0065 * (sweep_25)  # sweep_25 in degrees

        for cl_val in cl:
            kc_cd0_wing = 2.859 * (cl_val / (math.cos(sweep_25 / 180. * math.pi)) ** 2) ** 3 \
                          - 1.849 * (cl_val / (
                math.cos(sweep_25 / 180. * math.pi)) ** 2) ** 2 + 0.382 * \
                          (cl_val / (
                              math.cos(sweep_25 / 180. * math.pi)) ** 2) + 0.06  # sweep factor

            cd0_wing = ((ke_cd0_wing + kc_cd0_wing) * k_phi_cd0_wing +
                        ki_arrow_cd0 + 1) * cf_wing_hs * wet_area_wing / wing_area
            cd0.append(cd0_wing)

        if self.low_speed_aero:
            outputs['cd0_wing_low_speed'] = cd0
        else:
            outputs['cd0_wing_high_speed'] = cd0
