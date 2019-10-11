"""
    Estimation of yawing moment due to sideslip
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


class ComputeCnBeta(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Yawing moment due to sideslip estimation """

    def setup(self):

        self.add_input('geometry:fuselage_width_max', val=np.nan, units='m')
        self.add_input('geometry:fuselage_height_max', val=np.nan, units='m')
        self.add_input('geometry:fuselage_length', val=np.nan, units='m')
        self.add_input('geometry:fuselage_LAV', val=np.nan, units='m')
        self.add_input('geometry:fuselage_LAR', val=np.nan, units='m')
        self.add_input('tlar:cruise_Mach', val=np.nan)
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:wing_span', val=np.nan, units='m')

        self.add_output('dcn_beta')

        self.declare_partials('dcn_beta', '*', method='fd')

    def compute(self, inputs, outputs):
        fus_length = inputs['geometry:fuselage_length']
        lav = inputs['geometry:fuselage_LAV']
        lar = inputs['geometry:fuselage_LAR']
        width_max = inputs['geometry:fuselage_width_max']
        height_max = inputs['geometry:fuselage_height_max']
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        cruise_mach = inputs['tlar:cruise_Mach']

        l_f = math.sqrt(width_max * height_max)
        l_cyc = fus_length - lav - lar
        # estimation of fuselage volume
        volume_fus = math.pi * l_f**2 / 4 * (0.7 * lav + 0.5 * lar + l_cyc)
        # equation from raymer book eqn. 16.47
        cn_beta_fus = -1.3 * volume_fus / \
            wing_area / span * (l_f / width_max)
        cn_beta_goal = 0.0569 - 0.01694 * cruise_mach + 0.15904 * cruise_mach**2

        outputs['dcn_beta'] = cn_beta_goal - cn_beta_fus
