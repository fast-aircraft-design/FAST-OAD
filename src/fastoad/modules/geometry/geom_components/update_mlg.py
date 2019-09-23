"""
    Estimation of main landing gear center of gravity
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


class UpdateMLG(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Main landing gear center of gravity estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_l0', val=np.nan, units='m')
        self.add_input('geometry:wing_position', val=np.nan, units='m')
        self.add_input('cg_ratio', val=np.nan)
        self.add_input('delta_lg', val=np.nan)

        self.add_output('cg_airframe:A51', units='m')

        self.declare_partials('cg_airframe:A51', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        l0_wing = inputs['geometry:wing_l0']
        fa_length = inputs['geometry:wing_position']
        cg_ratio = inputs['cg_ratio']
        delta_lg = inputs['delta_lg']

        x_cg = fa_length - 0.25 * l0_wing + cg_ratio * l0_wing

        cg_airframe_a51 = x_cg + 0.08 * delta_lg

        outputs['cg_airframe:A51'] = cg_airframe_a51
