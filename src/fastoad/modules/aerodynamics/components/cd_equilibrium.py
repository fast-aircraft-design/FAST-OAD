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

from openmdao.core.explicitcomponent import ExplicitComponent


class CdEquilibrium(ExplicitComponent):
    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        if self.low_speed_aero:
            self.add_input('cl_low_speed', shape=(150))
            self.add_output('cd_eq_low_speed', shape=(150))
        else:
            self.add_input('cl_high_speed', shape=(150))
            self.add_output('cd_eq_high_speed', shape=(150))

    def compute(self, inputs, outputs):
        if self.low_speed_aero:
            cl = inputs['cl_low_speed']
        else:
            cl = inputs['cl_high_speed']

        cd_eq = []

        for cl_val in cl:
            cd_eq.append(5.89 * pow(10, -4) * cl_val)

        if self.low_speed_aero:
            outputs['cd_eq_low_speed'] = cd_eq
        else:
            outputs['cd_eq_high_speed'] = cd_eq
