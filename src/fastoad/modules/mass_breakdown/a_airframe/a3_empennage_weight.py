"""
Estimation of empennage weight
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

from fastoad.modules.mass_breakdown.options import TAIL_TYPE_OPTION, ENGINE_LOCATION_OPTION


class EmpennageWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing weight estimation (A3) """

    def initialize(self):
        self.options.declare(ENGINE_LOCATION_OPTION, types=float, default=1.0)
        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.)

    def setup(self):
        self.add_input('geometry:horizontal_tail:area', val=np.nan, units='m**2')
        self.add_input('geometry:vertical_tail:area', val=np.nan, units='m**2')
        self.add_input('weight:airframe:tail_plane:horizontal:mass:k', val=1.)
        self.add_input('weight:airframe:tail_plane:horizontal:mass:offset', val=0., units='kg')
        self.add_input('weight:airframe:tail_plane:vertical:mass:k', val=1.)
        self.add_input('weight:airframe:tail_plane:vertical:mass:offset', val=0., units='kg')

        self.add_output('weight:airframe:tail_plane:horizontal:mass', units='kg')
        self.add_output('weight:airframe:tail_plane:vertical:mass', units='kg')

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        ht_area = inputs['geometry:horizontal_tail:area']
        vt_area = inputs['geometry:vertical_tail:area']
        k_a31 = inputs['weight:airframe:tail_plane:horizontal:mass:k']
        offset_a31 = inputs['weight:airframe:tail_plane:horizontal:mass:offset']
        k_a32 = inputs['weight:airframe:tail_plane:vertical:mass:k']
        offset_a32 = inputs['weight:airframe:tail_plane:vertical:mass:offset']

        k_tail = 1.3 if self.options[TAIL_TYPE_OPTION] == 1 else 1.

        # Mass of the horizontal tail plane
        temp_a31 = ht_area * (14.4 + 0.155 * ht_area) * k_tail
        outputs['weight:airframe:tail_plane:horizontal:mass'] = k_a31 * temp_a31 + offset_a31

        # Mass of the vertical tail plane
        k_engine = 1 if self.options[ENGINE_LOCATION_OPTION] == 1. else 1.5

        temp_a32 = vt_area * (15.45 + 0.202 * vt_area) * k_engine * k_tail
        outputs['weight:airframe:tail_plane:vertical:mass'] = k_a32 * temp_a32 + offset_a32
