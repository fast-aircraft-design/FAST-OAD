"""
    Estimation of wing center of gravity
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

class ComputeWingCG(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing center of gravity estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_break', val=np.nan)
        self.add_input('geometry:wing_front_spar_ratio_root', val=np.nan)
        self.add_input('geometry:wing_front_spar_ratio_kink', val=np.nan)
        self.add_input('geometry:wing_front_spar_ratio_tip', val=np.nan)
        self.add_input('geometry:wing_rear_spar_ratio_root', val=np.nan)
        self.add_input('geometry:wing_rear_spar_ratio_kink', val=np.nan)
        self.add_input('geometry:wing_rear_spar_ratio_tip', val=np.nan)
        self.add_input('geometry:wing_span', val=np.nan, units='m')
        self.add_input('geometry:wing_x0', val=np.nan, units='m')
        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:wing_l3', val=np.nan, units='m')
        self.add_input('geometry:wing_l4', val=np.nan, units='m')
        self.add_input('geometry:wing_y2', val=np.nan, units='m')
        self.add_input('geometry:wing_x3', val=np.nan, units='m')
        self.add_input('geometry:wing_y3', val=np.nan, units='m')
        self.add_input('geometry:wing_x4', val=np.nan, units='m')
        self.add_input('geometry:wing_y4', val=np.nan, units='m')
        self.add_input('geometry:wing_position', val=np.nan, units='m')

        self.add_output('cg_airframe:A1', units='m')

        self.declare_partials('cg_airframe:A1', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        wing_break = inputs['geometry:wing_break']
        front_spar_ratio_root = inputs['geometry:wing_front_spar_ratio_root']
        front_spar_ratio_middle = inputs['geometry:wing_front_spar_ratio_kink']
        front_spar_ratio_tip = inputs['geometry:wing_front_spar_ratio_tip']
        rear_spar_ratio_root = inputs['geometry:wing_rear_spar_ratio_root']
        rear_spar_ratio_middle = inputs['geometry:wing_rear_spar_ratio_kink']
        rear_spar_ratio_tip = inputs['geometry:wing_rear_spar_ratio_tip']
        span = inputs['geometry:wing_span']
        x0_wing = inputs['geometry:wing_x0']
        l2_wing = inputs['geometry:wing_l2']
        l3_wing = inputs['geometry:wing_l3']
        l4_wing = inputs['geometry:wing_l4']
        y2_wing = inputs['geometry:wing_y2']
        x3_wing = inputs['geometry:wing_x3']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        x4_wing = inputs['geometry:wing_x4']
        fa_length = inputs['geometry:wing_position']

        if wing_break >= 0.35:
            y_cg = span / 2 * 0.35
            l_cg = (y3_wing - y_cg) / (y3_wing - y2_wing) * \
                (l2_wing - l3_wing) + l3_wing
            front_spar_cg = (y3_wing - y_cg) / \
                (y3_wing - y2_wing) * (l2_wing * front_spar_ratio_root -
                                       l3_wing * front_spar_ratio_middle) + \
                l3_wing * front_spar_ratio_middle
            rear_spar_cg = (y3_wing - y_cg) / \
                (y3_wing - y2_wing) * (l2_wing * rear_spar_ratio_root -
                                       l3_wing * rear_spar_ratio_middle) + \
                l3_wing * rear_spar_ratio_middle
            x_cg = (y_cg - y2_wing) / (y3_wing - y2_wing) * x3_wing + \
                front_spar_cg + (l_cg - front_spar_cg - rear_spar_cg) * 0.7
        elif wing_break < 0.35:
            y_cg = span / 2 * 0.35
            l_cg = (y4_wing - y_cg) / (y4_wing - y3_wing) * \
                (l3_wing - l4_wing) + l4_wing
            front_spar_cg = (y4_wing - y_cg) / \
                (y4_wing - y3_wing) * (l3_wing *
                                       front_spar_ratio_middle -
                                       l4_wing * front_spar_ratio_tip) + \
                l4_wing * front_spar_ratio_tip
            rear_spar_cg = (y4_wing - y_cg) / \
                (y4_wing - y3_wing) * (l3_wing *
                                       rear_spar_ratio_middle -
                                       l4_wing * rear_spar_ratio_tip) + \
                l4_wing * rear_spar_ratio_tip

            x_cg = (y_cg - y3_wing) / (y4_wing - y3_wing) * x4_wing + \
                front_spar_cg + (l_cg - front_spar_cg - rear_spar_cg) * 0.7
        x_cg_absolute = fa_length - 0.25 * x0_wing + (x_cg - x0_wing)

        outputs['cg_airframe:A1'] = x_cg_absolute
