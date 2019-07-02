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

from fastoad.utils.physics import Atmosphere


class Prepare2dRun(ExplicitComponent):

    def setup(self):
        self.add_input('geometry:wing_l0', val=4.2)
        self.add_input('tlar:v_approach', val=132.)
        self.add_output('xfoil:reynolds', val=1e7)
        self.add_output('xfoil:mach', val=0.2)

    def compute(self, inputs, outputs):
        l0_wing = inputs['geometry:wing_l0']
        speed = inputs['tlar:v_approach']
        speed *= 0.5144

        atm = Atmosphere(0., 15.)
        viscosity = atm.kinematic_viscosity
        speed_of_sound = atm.speed_of_sound

        mach = speed / speed_of_sound
        reynolds = speed * l0_wing / viscosity

        outputs['xfoil:mach'] = mach
        outputs['xfoil:reynolds'] = reynolds
