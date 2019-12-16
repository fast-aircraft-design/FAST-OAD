"""
    Estimation of vertical tail distance
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

from fastoad.modules.geometry.options import AIRCRAFT_FAMILY_OPTION, TAIL_TYPE_OPTION


class ComputeVTDistance(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail distance estimation """

    def initialize(self):
        self.options.declare(AIRCRAFT_FAMILY_OPTION, types=float, default=1.)
        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.)

        self.ac_family = self.options[AIRCRAFT_FAMILY_OPTION]
        self.tail_type = self.options[TAIL_TYPE_OPTION]

    def setup(self):

        self.add_input('geometry:fuselage:length', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:x', val=np.nan, units='m')

        self.add_output('geometry:vertical_tail:distance_from_wing', units='m')
        self.add_output('k_ar_effective')

        self.declare_partials('geometry:vertical_tail:distance_from_wing',
                              ['geometry:fuselage:length', 'geometry:wing:MAC:x'],
                              method='fd')

    def compute(self, inputs, outputs):
        fus_length = inputs['geometry:fuselage:length']
        fa_length = inputs['geometry:wing:MAC:x']

        if self.tail_type == 1.0:
            if self.ac_family == 1.0:
                lp_vt = 0.93 * fus_length - fa_length
                k_ar_effective = 2.9
            elif self.ac_family == 2.0:
                lp_vt = 6.6
                k_ar_effective = 2.9
        else:
            lp_vt = 0.88 * fus_length - fa_length
            k_ar_effective = 1.55

        outputs['geometry:vertical_tail:distance_from_wing'] = lp_vt
        outputs['k_ar_effective'] = k_ar_effective
