"""
Estimation of static margin
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
import openmdao.api as om


class ComputeStaticMargin(om.ExplicitComponent):
    """
    Computation of static margin i.e. difference between CG ratio and neutral
    point.

    If option 'target' is provided, this module will provide the output
    `data:handling_qualities:static_margin:to_target` that can be used as
    objective function in an optimization problem.
    """

    def initialize(self):
        self.options.declare('target', types=float, allow_none=True, default=None)

    def setup(self):
        self.add_input('data:weight:aircraft:CG:aft:MAC_position', val=np.nan)
        self.add_input('data:aerodynamics:cruise:neutral_point:x', val=np.nan)

        self.add_output('data:handling_qualities:static_margin')
        if self.options['target']:
            self.add_output('data:handling_qualities:static_margin:to_target',
                            desc='objective function to minimize to 0. for getting '
                                 'static margin close to fixed target (equal to the '
                                 'square of 100 times the difference to target)')

        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        cg_ratio = inputs['data:weight:aircraft:CG:aft:MAC_position']
        ac_ratio = inputs['data:aerodynamics:cruise:neutral_point:x']

        outputs['data:handling_qualities:static_margin'] = ac_ratio - cg_ratio

        if self.options['target']:
            outputs['data:handling_qualities:static_margin:to_target'] = \
                (100 * (self.options['target']
                        - outputs['data:handling_qualities:static_margin'])
                 ) ** 2
