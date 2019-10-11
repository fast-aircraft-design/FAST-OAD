"""
    Estimation of wing sweeps
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


class ComputeSweepWing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing sweeps estimation """

    def setup(self):

        self.add_input('geometry:wing_x3', val=np.nan, units='m')
        self.add_input('geometry:wing_x4', val=np.nan, units='m')
        self.add_input('geometry:wing_y2', val=np.nan, units='m')
        self.add_input('geometry:wing_y3', val=np.nan, units='m')
        self.add_input('geometry:wing_y4', val=np.nan, units='m')
        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:wing_l3', val=np.nan, units='m')
        self.add_input('geometry:wing_l4', val=np.nan, units='m')

        self.add_output('geometry:wing_sweep_0', units='deg')
        self.add_output('geometry:wing_sweep_100_inner', units='deg')
        self.add_output('geometry:wing_sweep_100_outer', units='deg')

        self.declare_partials('geometry:wing_sweep_0', ['geometry:wing_x3',
                                                        'geometry:wing_y2',
                                                        'geometry:wing_y3'],
                              method='fd')
        self.declare_partials('geometry:wing_sweep_100_inner', ['geometry:wing_x3',
                                                                'geometry:wing_l2',
                                                                'geometry:wing_y2',
                                                                'geometry:wing_y3',
                                                                'geometry:wing_l3'],
                              method='fd')
        self.declare_partials('geometry:wing_sweep_100_outer', ['geometry:wing_x3',
                                                                'geometry:wing_x4',
                                                                'geometry:wing_y3',
                                                                'geometry:wing_y4',
                                                                'geometry:wing_l3',
                                                                'geometry:wing_l4'],
                              method='fd')

    def compute(self, inputs, outputs):
        x3_wing = inputs['geometry:wing_x3']
        x4_wing = inputs['geometry:wing_x4']
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        l2_wing = inputs['geometry:wing_l2']
        l3_wing = inputs['geometry:wing_l3']
        l4_wing = inputs['geometry:wing_l4']

        outputs['geometry:wing_sweep_0'] = math.atan(x3_wing / (y3_wing - y2_wing)) / math.pi * 180.
        outputs['geometry:wing_sweep_100_inner'] = math.atan(
            (x3_wing + l3_wing - l2_wing) / (y3_wing - y2_wing)) / math.pi * 180
        outputs['geometry:wing_sweep_100_outer'] = math.atan(
            (x4_wing + l4_wing - x3_wing - l3_wing) / (y4_wing - y3_wing)) / math.pi * 180.
