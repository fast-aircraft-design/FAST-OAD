"""
    Estimation of horizontal tail area
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

from fastoad.modules.geometry.options import AIRCRAFT_FAMILY_OPTION, TAIL_TYPE_OPTION

class ComputeHTArea(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail area estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

        self.options.declare(AIRCRAFT_FAMILY_OPTION, types=float, default=1.)
        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.)

        self.ac_family = self.options[AIRCRAFT_FAMILY_OPTION]
        self.tail_type = self.options[TAIL_TYPE_OPTION]

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:fuselage_length', val=np.nan, units='m')
        self.add_input('geometry:wing_position', val=np.nan, units='m')
        self.add_input('geometry:ht_vol_coeff', val=np.nan)
        self.add_input('geometry:wing_l0', val=np.nan, units='m')
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:ht_area', val=np.nan, units='m**2')

        self.add_output('geometry:ht_lp', units='m')
        self.add_output('geometry:ht_wet_area', units='m**2')
        self.add_output('delta_cm_takeoff')

        self.declare_partials('geometry:ht_lp',
                              ['geometry:fuselage_length', 'geometry:wing_position'],
                              method=deriv_method)
        self.declare_partials('geometry:ht_wet_area', 'geometry:ht_area', method=deriv_method)
        self.declare_partials('delta_cm_takeoff', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        fus_length = inputs['geometry:fuselage_length']
        fa_length = inputs['geometry:wing_position']
        wing_area = inputs['geometry:wing_area']
        l0_wing = inputs['geometry:wing_l0']
        s_h = inputs['geometry:ht_area']
        ht_vol_coeff = inputs['geometry:ht_vol_coeff']

        if self.tail_type == 1.0:
            if self.ac_family == 1.0:
                lp_ht = fus_length - fa_length
            elif self.ac_family == 2.0:
                lp_ht = 7.7
        else:
            lp_ht = 0.91 * fus_length - fa_length

        if self.tail_type == 0.:
            wet_area_ht = 2 * s_h
        elif self.tail_type == 1.:
            wet_area_ht = 2 * 0.8 * s_h
        else:
            print('Error in the tailplane positioning')

        delta_cm_takeoff = s_h * lp_ht / wing_area / l0_wing - ht_vol_coeff

        outputs['geometry:ht_lp'] = lp_ht
        outputs['geometry:ht_wet_area'] = wet_area_ht
        outputs['delta_cm_takeoff'] = delta_cm_takeoff
