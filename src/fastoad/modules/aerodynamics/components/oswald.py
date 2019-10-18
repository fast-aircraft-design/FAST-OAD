"""
Computation of Oswald coefficient
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
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class OswaldCoefficient(ExplicitComponent):
    # TODO: Document equations. Cite sources (M. Nita and D. Scholz)
    # FIXME: output the real Oswald coefficient (coef_e instead of coef_k)
    """ Computes Oswald efficiency number """

    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:wing_span', val=np.nan, units='m')
        self.add_input('geometry:fuselage_height_max', val=np.nan, units='m')
        self.add_input('geometry:fuselage_width_max', val=np.nan, units='m')
        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:wing_l4', val=np.nan, units='m')
        self.add_input('geometry:wing_sweep_25', val=np.nan, units='deg')

        if self.options['low_speed_aero']:
            self.add_input('Mach_low_speed', val=np.nan)
            self.add_output('oswald_coeff_low_speed', val=np.nan)
        else:
            self.add_input('tlar:cruise_Mach', val=np.nan)
            self.add_output('oswald_coeff_high_speed', val=np.nan)


    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span'] / math.cos(5. / 180 * math.pi)
        height_fus = inputs['geometry:fuselage_height_max']
        width_fus = inputs['geometry:fuselage_width_max']
        l2_wing = inputs['geometry:wing_l2']
        l4_wing = inputs['geometry:wing_l4']
        sweep_25 = inputs['geometry:wing_sweep_25']
        if self.options['low_speed_aero']:
            mach = inputs['Mach_low_speed']
        else:
            mach = inputs['tlar:cruise_Mach']

        aspect_ratio = span ** 2 / wing_area
        df = math.sqrt(width_fus * height_fus)
        lamda = l4_wing / l2_wing
        delta_lamda = -0.357 + 0.45 * \
                      math.exp(0.0375 * sweep_25 / 180. * math.pi)
        lamda = lamda - delta_lamda
        f_lamda = 0.0524 * lamda ** 4 - 0.15 * lamda ** 3 + \
                  0.1659 * lamda ** 2 - 0.0706 * lamda + 0.0119
        e_theory = 1 / (1 + f_lamda * aspect_ratio)

        if mach <= 0.4:
            ke_m = 1.
        else:
            ke_m = -0.001521 * ((mach - 0.05) / 0.3 - 1) ** 10.82 + 1

        ke_f = 1 - 2 * (df / span) ** 2
        coef_e = e_theory * ke_f * ke_m * 0.9
        coef_k = 1. / (math.pi * aspect_ratio * coef_e)

        if self.options['low_speed_aero']:
            outputs['oswald_coeff_low_speed'] = coef_k
        else:
            outputs['oswald_coeff_high_speed'] = coef_k
