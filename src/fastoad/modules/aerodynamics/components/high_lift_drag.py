"""
Computation of drag increment due to high-lift devices
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


class DeltaCDHighLift(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """
    Component for getting drag increment for given slta/flap configuration
    """
    def setup(self):
        self.add_input('flap_angle', val=np.nan, units='deg')
        self.add_input('slat_angle', val=np.nan, units='deg')
        self.add_output('delta_cd', val=np.nan)

        self.add_input('geometry:flap_span_ratio', val=np.nan)
        self.add_input('geometry:slat_span_ratio', val=np.nan)

    def compute(self, inputs, outputs):
        slat_angle = inputs['slat_angle']
        flap_angle = inputs['flap_angle']

        slat_span_ratio = inputs['geometry:slat_span_ratio']
        flap_span_ratio = inputs['geometry:flap_span_ratio']

        cd0_slat = (-0.00266 + 0.06065 * slat_angle - 0.03023 * slat_angle ** 2 +
                    0.01055 * slat_angle ** 3 - 0.00176 * slat_angle ** 4 +
                    1.77986E-4 * slat_angle ** 5 - 1.11754E-5 * slat_angle ** 6 +
                    4.19082E-7 * slat_angle ** 7 - 8.53492E-9 * slat_angle ** 8 +
                    7.24194E-11 * slat_angle ** 9) * \
                   slat_span_ratio / 100
        cd0_flap = (-0.01523 + 0.05145 * flap_angle - 9.53201E-4 * flap_angle ** 2 +
                    7.5972E-5 * flap_angle ** 3) * \
                   flap_span_ratio / 100
        total_cd0 = cd0_flap + cd0_slat

        outputs['delta_cd'] = total_cd0
