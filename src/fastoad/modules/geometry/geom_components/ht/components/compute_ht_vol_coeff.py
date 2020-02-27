"""
    Estimation of horizontal tail volume coefficient
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
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent

from fastoad.utils.physics.atmosphere import Atmosphere


class ComputeHTVolCoeff(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail volume coefficient estimation """

    def setup(self):
        self.add_input('data:weight:airframe:landing_gear:main:CG:x', val=np.nan, units='m')
        self.add_input('data:weight:airframe:landing_gear:front:CG:x', val=np.nan, units='m')
        self.add_input('data:weight:aircraft:MTOW', val=np.nan, units='kg')
        self.add_input('data:geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('data:geometry:wing:MAC:length', val=np.nan, units='m')
        self.add_input('data:requirements:CG_range', val=np.nan)

        self.add_output('data:geometry:landing_gear:front:distance_to_main')
        self.add_output('data:geometry:horizontal_tail:volume_coefficient')

        self.declare_partials('data:geometry:landing_gear:front:distance_to_main',
                              ['data:weight:airframe:landing_gear:main:CG:x',
                               'data:weight:airframe:landing_gear:front:CG:x'],
                              method='fd')
        self.declare_partials('data:geometry:horizontal_tail:volume_coefficient', '*', method='fd')

    def compute(self, inputs, outputs):
        cg_a51 = inputs['data:weight:airframe:landing_gear:main:CG:x']
        cg_a52 = inputs['data:weight:airframe:landing_gear:front:CG:x']
        mtow = inputs['data:weight:aircraft:MTOW']
        wing_area = inputs['data:geometry:wing:area']
        l0_wing = inputs['data:geometry:wing:MAC:length']
        required_cg_range = inputs['data:requirements:CG_range']

        delta_lg = cg_a51 - cg_a52
        atm = Atmosphere(0.)
        rho = atm.density
        sos = atm.speed_of_sound
        vspeed = sos * 0.2  # assume the corresponding Mach of VR is 0.2

        cm_wheel = 0.08 * delta_lg * mtow * 9.81 / \
                   (0.5 * rho * vspeed ** 2 * wing_area * l0_wing)
        delta_cm = mtow * l0_wing * required_cg_range * \
                   9.81 / (0.5 * rho * vspeed ** 2 * wing_area * l0_wing)
        ht_vol_coeff = cm_wheel + delta_cm
        outputs['data:geometry:landing_gear:front:distance_to_main'] = delta_lg
        outputs['data:geometry:horizontal_tail:volume_coefficient'] = ht_vol_coeff
