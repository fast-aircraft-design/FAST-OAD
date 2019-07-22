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

from fastoad.utils.physics import Atmosphere


class ComputeReynolds(ExplicitComponent):

    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        if self.low_speed_aero:
            self.add_input('Mach_low_speed', val=np.nan)
            self.add_output('reynolds_low_speed')
        else:
            self.add_input('tlar:cruise_Mach', val=np.nan)
            self.add_input('sizing_mission:cruise_altitude', val=np.nan)
            self.add_output('reynolds_high_speed')

    def compute(self, inputs, outputs):
        if self.low_speed_aero:
            mach = inputs['Mach_low_speed']
            altitude = 0.
        else:
            mach = inputs['tlar:cruise_Mach']
            altitude = inputs['sizing_mission:cruise_altitude']

        atm = Atmosphere(altitude)
        t = atm.temperature
        ps = t * atm.density * 287.1

        if self.low_speed_aero:
            outputs['reynolds_low_speed'] = 47899 * (
                    ps * mach * ((1 + 0.126 * mach ** 2) * t + 110.4)
            ) / (t ** 2 * (1 + 0.126 * mach ** 2) ** (5 / 2))
        else:
            outputs['reynolds_high_speed'] = 47899 * (
                    ps * mach * ((1 + 0.126 * mach ** 2) * t + 110.4)
            ) / (t ** 2 * (1 + 0.126 * mach ** 2) ** (5 / 2))
