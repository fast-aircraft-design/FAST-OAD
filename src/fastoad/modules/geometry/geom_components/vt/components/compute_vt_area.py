"""
    Estimation of vertical tail area
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


class ComputeVTArea(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail area estimation """

    def setup(self):
        self.add_input('TLAR:cruise_mach', val=np.nan)
        self.add_input('cg_ratio', val=np.nan)
        self.add_input('aerodynamics:fuselage:cruise:CnBeta', val=np.nan)
        self.add_input('aerodynamics:vertical_tail:cruise:CL_alpha', val=np.nan)
        self.add_input('geometry:wing:MAC:length', val=np.nan, units='m')
        self.add_input('geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('geometry:wing:span', val=np.nan, units='m')
        self.add_input('geometry:vertical_tail:distance_from_wing', val=np.nan, units='m')

        self.add_output('geometry:vertical_tail:wetted_area', units='m**2')
        self.add_output('geometry:vertical_tail:area', units='m**2')
        self.add_output('aerodynamics:vertical_tail:cruise:CnBeta', units='m**2')

        self.declare_partials('geometry:vertical_tail:wetted_area', '*', method='fd')
        self.declare_partials('geometry:vertical_tail:area', '*', method='fd')
        self.declare_partials('aerodynamics:vertical_tail:cruise:CnBeta', '*', method='fd')

    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing:area']
        span = inputs['geometry:wing:span']
        l0_wing = inputs['geometry:wing:MAC:length']
        x_cg_plane = inputs['cg_ratio']
        cn_beta_fus = inputs['aerodynamics:fuselage:cruise:CnBeta']
        cl_alpha_vt = inputs['aerodynamics:vertical_tail:cruise:CL_alpha']
        lp_vt = inputs['geometry:vertical_tail:distance_from_wing']
        cruise_mach = inputs['TLAR:cruise_mach']

        cn_beta_goal = 0.0569 - 0.01694 * cruise_mach + 0.15904 * cruise_mach ** 2
        dcn_beta = cn_beta_goal - cn_beta_fus
        dxca_xcg = lp_vt + 0.25 * l0_wing - x_cg_plane * l0_wing
        s_v = dcn_beta / (dxca_xcg / wing_area / span * cl_alpha_vt)
        wet_area_vt = 2.1 * s_v

        outputs['geometry:vertical_tail:wetted_area'] = wet_area_vt
        outputs['geometry:vertical_tail:area'] = s_v
        outputs['aerodynamics:vertical_tail:cruise:CnBeta'] = dcn_beta
