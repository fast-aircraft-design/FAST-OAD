"""
    Estimation of horizontal tail sweeps
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


class ComputeHTSweep(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail sweeps estimation """

    def setup(self):

        self.add_input('geometry:ht_root_chord', val=np.nan, units='m')
        self.add_input('geometry:ht_tip_chord', val=np.nan, units='m')
        self.add_input('geometry:ht_span', val=np.nan, units='m')
        self.add_input('geometry:ht_sweep_25', val=np.nan, units='deg')

        self.add_output('geometry:ht_sweep_0', units='deg')
        self.add_output('geometry:ht_sweep_100', units='deg')

        self.declare_partials('geometry:ht_sweep_0', '*', method='fd')
        self.declare_partials('geometry:ht_sweep_100', '*', method='fd')

    def compute(self, inputs, outputs):
        b_h = inputs['geometry:ht_span']
        root_chord = inputs['geometry:ht_root_chord']
        tip_chord = inputs['geometry:ht_tip_chord']
        sweep_25_ht = inputs['geometry:ht_sweep_25']

        half_span = b_h / 2.
        # TODO: The unit conversion can be handled by OpenMDAO
        sweep_0_ht = (math.pi / 2 -
                      math.atan(half_span /
                                (0.25 * root_chord - 0.25 *
                                 tip_chord + half_span *
                                 math.tan(sweep_25_ht / 180. * math.pi)))) / math.pi * 180.
        sweep_100_ht = (math.pi / 2 - math.atan(half_span / (half_span * math.tan(
            sweep_25_ht / 180. * math.pi) - 0.75 * root_chord + 0.75 * tip_chord))) / math.pi * 180.

        outputs['geometry:ht_sweep_0'] = sweep_0_ht
        outputs['geometry:ht_sweep_100'] = sweep_100_ht
