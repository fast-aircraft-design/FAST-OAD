"""
    Estimation of horizontal tail area
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
import openmdao.api as om

from fastoad.modules.options import AIRCRAFT_FAMILY_OPTION, TAIL_TYPE_OPTION
from fastoad.utils.physics import Atmosphere


class ComputeHTArea(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail area estimation """

    def initialize(self):
        self.options.declare(AIRCRAFT_FAMILY_OPTION, types=float, default=1.)
        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.)

    def setup(self):

        self.add_input('data:geometry:fuselage:length', val=np.nan, units='m')
        self.add_input('data:geometry:wing:MAC:x', val=np.nan, units='m')
        self.add_input('data:geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('data:geometry:wing:MAC:length', val=np.nan, units='m')
        self.add_input('data:weight:airframe:landing_gear:main:CG:x', val=np.nan, units='m')
        self.add_input('data:weight:airframe:landing_gear:front:CG:x', val=np.nan, units='m')
        self.add_input('data:weight:aircraft:MTOW', val=np.nan, units='kg')
        self.add_input('data:requirements:CG_range', val=np.nan)

        self.add_output('data:geometry:horizontal_tail:distance_from_wing', units='m')
        self.add_output('data:geometry:horizontal_tail:wetted_area', units='m**2')
        self.add_output('data:geometry:horizontal_tail:area', units='m**2')

        self.declare_partials('data:geometry:horizontal_tail:distance_from_wing',
                              ['data:geometry:fuselage:length', 'data:geometry:wing:MAC:x'],
                              method='fd')
        self.declare_partials('data:geometry:horizontal_tail:wetted_area', '*', method='fd')
        self.declare_partials('data:geometry:horizontal_tail:area', '*', method='fd')

    def compute(self, inputs, outputs):
        tail_type = self.options[TAIL_TYPE_OPTION]
        ac_family = self.options[AIRCRAFT_FAMILY_OPTION]

        fus_length = inputs['data:geometry:fuselage:length']
        fa_length = inputs['data:geometry:wing:MAC:x']
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

        if tail_type == 1.0:
            if ac_family == 1.0:
                lp_ht = fus_length - fa_length
            elif ac_family == 2.0:
                # TODO: remove this hard coded value
                lp_ht = 7.7
        else:
            lp_ht = 0.91 * fus_length - fa_length

        s_h = ht_vol_coeff / (lp_ht / wing_area / l0_wing)

        if tail_type == 0.:
            wet_area_ht = 2 * s_h
        elif tail_type == 1.:
            wet_area_ht = 2 * 0.8 * s_h
        else:
            print('Error in the tailplane positioning')

        outputs['data:geometry:horizontal_tail:distance_from_wing'] = lp_ht
        outputs['data:geometry:horizontal_tail:wetted_area'] = wet_area_ht
        outputs['data:geometry:horizontal_tail:area'] = s_h
