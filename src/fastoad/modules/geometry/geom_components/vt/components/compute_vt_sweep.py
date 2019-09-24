"""
    Estimation of vertical tail sweeps
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


class ComputeVTSweep(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail sweeps estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:vt_span', val=np.nan, units='m')
        self.add_input('geometry:vt_root_chord', val=np.nan, units='m')
        self.add_input('geometry:vt_tip_chord', val=np.nan, units='m')
        self.add_input('geometry:vt_sweep_25', val=np.nan, units='deg')

        self.add_output('geometry:vt_sweep_0', units='deg')
        self.add_output('geometry:vt_sweep_100', units='deg')

        self.declare_partials('geometry:vt_sweep_0', '*', method=deriv_method)
        self.declare_partials('geometry:vt_sweep_100', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        root_chord = inputs['geometry:vt_root_chord']
        tip_chord = inputs['geometry:vt_tip_chord']
        sweep_25_vt = inputs['geometry:vt_sweep_25']
        b_v = inputs['geometry:vt_span']

        sweep_0_vt = (math.pi / 2 -
                      math.atan(b_v / (0.25 * root_chord - 0.25 *
                                       tip_chord + b_v *
                                       math.tan(sweep_25_vt / 180. * math.pi)))) / math.pi * 180.
        sweep_100_vt = (math.pi / 2 -
                        math.atan(b_v / (b_v * math.tan(sweep_25_vt /
                                                        180. * math.pi) - 0.75 *
                                         root_chord + 0.75 * tip_chord))) / math.pi * 180.

        outputs['geometry:vt_sweep_0'] = sweep_0_vt
        outputs['geometry:vt_sweep_100'] = sweep_100_vt
