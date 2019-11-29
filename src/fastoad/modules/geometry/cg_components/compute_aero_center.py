"""
    Estimation of aerodynamic center
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


class ComputeAeroCenter(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Aerodynamic center estimation """

    def setup(self):

        self.add_input('geometry:wing:root:leading_edge:x', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:length', val=np.nan, units='m')
        self.add_input('geometry:wing:l1', val=np.nan, units='m')
        self.add_input('geometry:fuselage:maximum_width', val=np.nan, units='m')
        self.add_input('geometry:fuselage:length', val=np.nan, units='m')
        self.add_input('geometry:wing:location', val=np.nan, units='m')
        self.add_input('geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('geometry:horizontal_tail:area', val=np.nan, units='m**2')
        self.add_input('geometry:horizontal_tail:distance_from_wing', val=np.nan, units='m')
        self.add_input('aerodynamics:aircraft:cruise:CL_alpha', val=np.nan)
        self.add_input('aerodynamics:horizontal_tail:cruise:CL_alpha', val=np.nan)

        self.add_output('x_ac_ratio')

        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        x0_wing = inputs['geometry:wing:root:leading_edge:x']
        l0_wing = inputs['geometry:wing:MAC:length']
        l1_wing = inputs['geometry:wing:l1']
        width_max = inputs['geometry:fuselage:maximum_width']
        fa_length = inputs['geometry:wing:location']
        fus_length = inputs['geometry:fuselage:length']
        wing_area = inputs['geometry:wing:area']
        s_h = inputs['geometry:horizontal_tail:area']
        lp_ht = inputs['geometry:horizontal_tail:distance_from_wing']
        cl_alpha_wing = inputs['aerodynamics:aircraft:cruise:CL_alpha']
        cl_alpha_ht = inputs['aerodynamics:horizontal_tail:cruise:CL_alpha']
        # TODO: make variable name is computation sequence more english
        x0_25 = fa_length - 0.25 * l0_wing - x0_wing + 0.25 * l1_wing
        ratio_x025 = x0_25 / fus_length
        # fitting result of Raymer book, figure 16.14
        k_h = 0.01222 - 7.40541E-4 * ratio_x025 * 100 + 2.1956E-5 * (ratio_x025 * 100)**2
        # equation from Raymer book, eqn 16.22
        cm_alpha_fus = k_h * width_max**2 * \
            fus_length / (l0_wing * wing_area) * 180. / np.pi
        x_ca_plane = (cl_alpha_wing * fa_length / l0_wing - cm_alpha_fus +
                      cl_alpha_ht * (1 - 0.4) * 0.9 *
                      s_h / wing_area * (lp_ht + fa_length) / l0_wing) / \
                     (cl_alpha_wing +
                      cl_alpha_ht * (1 - 0.4) * 0.9 * s_h / wing_area)
        x_aero_center = x_ca_plane - fa_length / l0_wing + 0.25

        outputs['x_ac_ratio'] = x_aero_center
