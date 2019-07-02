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

from openmdao.core.explicitcomponent import ExplicitComponent


class Cd0Total(ExplicitComponent):
    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        self.add_input('geometry:S_total', val=800.)

        if self.low_speed_aero:
            self.add_input('cd0_wing_low_speed', val=1e-4 * np.ones(150), shape=(150))
            self.add_input('cd0_fuselage_low_speed', val=1e-4 * np.ones(150), shape=(150))
            self.add_input('cd0_ht_low_speed', val=1e-4)
            self.add_input('cd0_vt_low_speed', val=1e-4)
            self.add_input('cd0_nacelle_low_speed', val=1e-4)
            self.add_input('cd0_pylon_low_speed', val=1e-4)
            self.add_output('cd0_total_low_speed', shape=(150))
        else:
            self.add_input('cd0_wing_high_speed', val=1e-4 * np.ones(150), shape=(150))
            self.add_input('cd0_fuselage_high_speed', val=1e-4 * np.ones(150), shape=(150))
            self.add_input('cd0_ht_high_speed', val=1e-4)
            self.add_input('cd0_vt_high_speed', val=1e-4)
            self.add_input('cd0_nacelle_high_speed', val=1e-4)
            self.add_input('cd0_pylon_high_speed', val=1e-4)
            self.add_output('cd0_total_high_speed', shape=(150))

    def compute(self, inputs, outputs):
        wet_area_total = inputs['geometry:S_total']
        if self.low_speed_aero:
            cd0_wing = inputs['cd0_wing_low_speed']
            cd0_fus = inputs['cd0_fuselage_low_speed']
            cd0_ht = inputs['cd0_ht_low_speed']
            cd0_vt = inputs['cd0_vt_low_speed']
            cd0_nac = inputs['cd0_nacelle_low_speed']
            cd0_pylon = inputs['cd0_pylon_low_speed']
        else:
            cd0_wing = inputs['cd0_wing_high_speed']
            cd0_fus = inputs['cd0_fuselage_high_speed']
            cd0_ht = inputs['cd0_ht_high_speed']
            cd0_vt = inputs['cd0_vt_high_speed']
            cd0_nac = inputs['cd0_nacelle_high_speed']
            cd0_pylon = inputs['cd0_pylon_high_speed']

        k_techno = 1
        k_parasite = - 2.39 * pow(10, -12) * wet_area_total ** 3 + 2.58 * pow(
            10, -8) * wet_area_total ** 2 - 0.89 * pow(10, -4) * wet_area_total + 0.163

        cd0_total = []
        for i, elem in enumerate(cd0_wing):
            cd0_total_hs = cd0_wing[i] + cd0_fus[i] + cd0_ht + cd0_vt + cd0_nac + cd0_pylon
            cd0_total.append(cd0_total_hs + k_parasite * k_techno * cd0_total_hs)

        if self.low_speed_aero:
            outputs['cd0_total_low_speed'] = cd0_total
        else:
            outputs['cd0_total_high_speed'] = cd0_total
