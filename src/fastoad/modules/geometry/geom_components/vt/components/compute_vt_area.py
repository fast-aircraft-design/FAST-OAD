"""
    Estimation of vertical tail area
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


class ComputeVTArea(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail area estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        #        self.add_input('geometry:wing_position', val=np.nan)
        self.add_input('cg_ratio', val=np.nan)
        self.add_input('geometry:wing_l0', val=np.nan, units='m')
        self.add_input('dcn_beta', val=np.nan)
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:wing_span', val=np.nan, units='m')
        self.add_input('geometry:vt_lp', val=np.nan, units='m')
        self.add_input('geometry:vt_area', val=np.nan, units='m**2')
        self.add_input('aerodynamics:Cl_alpha_vt', val=np.nan)

        self.add_output('geometry:vt_wet_area', units='m**2')
        self.add_output('delta_cn')

        self.declare_partials('geometry:vt_wet_area', 'geometry:vt_area')

        self.declare_partials('delta_cn', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        l0_wing = inputs['geometry:wing_l0']
        x_cg_plane = inputs['cg_ratio']
        s_v = inputs['geometry:vt_area']
        dcn_beta = inputs['dcn_beta']
        cl_alpha_vt = inputs['aerodynamics:Cl_alpha_vt']
        lp_vt = inputs['geometry:vt_lp']

        dxca_xcg = lp_vt + 0.25 * l0_wing - x_cg_plane * l0_wing
        delta_cn = s_v * dxca_xcg / wing_area / span * cl_alpha_vt - dcn_beta
        wet_area_vt = 2.1 * s_v

        outputs['geometry:vt_wet_area'] = wet_area_vt
        outputs['delta_cn'] = delta_cn
