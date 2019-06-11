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

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_x0', val=np.nan)
        self.add_input('geometry:wing_l0', val=np.nan)
        self.add_input('geometry:wing_l1', val=np.nan)
        self.add_input('geometry:fuselage_width_max', val=np.nan)
        self.add_input('geometry:fuselage_length', val=np.nan)
        self.add_input('geometry:wing_position', val=np.nan)
        self.add_input('geometry:wing_area', val=np.nan)
        self.add_input('geometry:ht_area', val=np.nan)
        self.add_input('geometry:ht_lp', val=np.nan)
        self.add_input('aerodynamics:Cl_alpha', val=np.nan)
        self.add_input('aerodynamics:Cl_alpha_ht', val=np.nan)

        self.add_output('x_ac_ratio')

        self.declare_partials('*', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        x0_wing = inputs['geometry:wing_x0']
        l0_wing = inputs['geometry:wing_l0']
        l1_wing = inputs['geometry:wing_l1']
        width_max = inputs['geometry:fuselage_width_max']
        fa_length = inputs['geometry:wing_position']
        fus_length = inputs['geometry:fuselage_length']
        wing_area = inputs['geometry:wing_area']
        s_h = inputs['geometry:ht_area']
        lp_ht = inputs['geometry:ht_lp']
        cl_alpha_wing = inputs['aerodynamics:Cl_alpha']
        cl_alpha_ht = inputs['aerodynamics:Cl_alpha_ht']

        x0_25 = fa_length - 0.25 * l0_wing - x0_wing + 0.25 * l1_wing
        ratio_x025 = x0_25 / fus_length
        # fitting result of Raymer book, figure 16.14
        k_h = 0.01222 - 7.40541E-4 * ratio_x025 + 2.1956E-5 * ratio_x025**2
        # equation from Raymer book, eqn 16.22
        cm_alpha_fus = k_h * width_max**2 * \
            fus_length / (l0_wing * wing_area) * 57.3
        x_ca_plane = (cl_alpha_wing * (fa_length - cm_alpha_fus / cl_alpha_wing) +
                      cl_alpha_ht * (1 - 0.4) * 0.9 *
                      s_h / wing_area * (lp_ht + fa_length)) / \
            (cl_alpha_wing +
             cl_alpha_ht * (1 - 0.4) * 0.9 * s_h / wing_area)
        x_aero_center = (x_ca_plane - fa_length + 0.25 * l0_wing) / l0_wing

        outputs['x_ac_ratio'] = x_aero_center
