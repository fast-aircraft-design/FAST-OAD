"""
    Estimation of center of gravity for load case 2
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

class ComputeCGLoadCase2(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Center of gravity estimation for load case 2 """

    def setup(self):

        self.add_input('geometry:wing_l0', val=np.nan, units='m')
        self.add_input('geometry:wing_position', val=np.nan, units='m')
        self.add_input('cg:cg_pax', val=np.nan, units='m')
        self.add_input('cg:cg_rear_fret', val=np.nan, units='m')
        self.add_input('cg:cg_front_fret', val=np.nan, units='m')
        self.add_input('tlar:NPAX', val=np.nan)
        self.add_input('weight:MFW', val=np.nan, units='kg')
        self.add_input('cg:cg_tank', val=np.nan, units='m')
        self.add_input('x_cg_plane_up', val=np.nan)
        self.add_input('x_cg_plane_down', val=np.nan)

        self.add_output('cg_ratio_lc2')

        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        l0_wing = inputs['geometry:wing_l0']
        fa_length = inputs['geometry:wing_position']
        cg_pax = inputs['cg:cg_pax']
        cg_rear_fret = inputs['cg:cg_rear_fret']
        cg_front_fret = inputs['cg:cg_front_fret']
        npax = inputs['tlar:NPAX']
        x_cg_plane_up = inputs['x_cg_plane_up']
        x_cg_plane_down = inputs['x_cg_plane_down']
        mfw = inputs['weight:MFW']
        cg_tank = inputs['cg:cg_tank']

        weight_pax = npax * 90.
        weight_rear_fret = npax * 20
        weight_front_fret = npax * 20
        weight_pl = weight_pax + weight_rear_fret + weight_front_fret
        x_cg_pl_2 = (weight_pax * cg_pax +
                     weight_rear_fret * cg_rear_fret +
                     weight_front_fret * cg_front_fret) / \
            (weight_pl)
        x_cg_plane_pl_2 = (x_cg_plane_up + weight_pl * x_cg_pl_2 +
                           mfw * cg_tank) / (x_cg_plane_down + weight_pl + mfw)  # forward
        cg_ratio_pl_2 = (x_cg_plane_pl_2 - fa_length + 0.25 * l0_wing) / l0_wing

        outputs['cg_ratio_lc2'] = cg_ratio_pl_2
