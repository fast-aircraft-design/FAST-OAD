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
from scipy.constants import g

from fastoad.modules.options import TAIL_TYPE_OPTION
from fastoad.utils.physics import Atmosphere


class ComputeHTArea(om.ExplicitComponent):
    """
    Computes area of horizontal tail plane

    Area is computed to fulfill aircraft balance requirement at rotation speed
    """

    def initialize(self):
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

        self.declare_partials('*', '*', method='fd')
        self.declare_partials('data:geometry:horizontal_tail:distance_from_wing',
                              ['data:geometry:fuselage:length', 'data:geometry:wing:MAC:x'],
                              method='fd')

    def compute(self, inputs, outputs):
        # Area of HTP is computed to balance aircraft at rotation speed, assuming that:
        # - CM from wing lift + aircraft weight is zero
        # - main landing gear supports MTOW

        tail_type = self.options[TAIL_TYPE_OPTION]

        fuselage_length = inputs['data:geometry:fuselage:length']
        x_wing_aero_center = inputs['data:geometry:wing:MAC:x']
        x_main_lg = inputs['data:weight:airframe:landing_gear:main:CG:x']
        x_front_lg = inputs['data:weight:airframe:landing_gear:front:CG:x']
        mtow = inputs['data:weight:aircraft:MTOW']
        wing_area = inputs['data:geometry:wing:area']
        wing_mac = inputs['data:geometry:wing:MAC:length']
        required_cg_range = inputs['data:requirements:CG_range']

        delta_lg = x_main_lg - x_front_lg
        atm = Atmosphere(0.)
        rho = atm.density
        vspeed = atm.speed_of_sound * 0.2  # assume the corresponding Mach of VR is 0.2

        pdyn = 0.5 * rho * vspeed ** 2
        # CM of MTOW on main landing gear w.r.t 25% wing MAC
        lever_arm = 0.08 * delta_lg  # lever arm wrt CoG
        lever_arm += wing_mac * required_cg_range  # and now wrt 25% wing MAC
        cm_wheel = mtow * g * lever_arm / (pdyn * wing_area * wing_mac)

        ht_volume_coeff = cm_wheel

        if tail_type == 1.0:
            aero_centers_distance = fuselage_length - x_wing_aero_center
            wet_area_coeff = 1.6
        else:
            aero_centers_distance = 0.91 * fuselage_length - x_wing_aero_center
            wet_area_coeff = 2.

        htp_area = ht_volume_coeff / aero_centers_distance * wing_area * wing_mac
        wet_area_htp = wet_area_coeff * htp_area

        outputs['data:geometry:horizontal_tail:distance_from_wing'] = aero_centers_distance
        outputs['data:geometry:horizontal_tail:wetted_area'] = wet_area_htp
        outputs['data:geometry:horizontal_tail:area'] = htp_area
