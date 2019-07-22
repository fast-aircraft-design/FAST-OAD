"""
    FAST - Copyright (c) 2016 ONERA ISAE
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
from math import pi
from openmdao.core.explicitcomponent import ExplicitComponent


class OswaldCoefficient(ExplicitComponent):

    def setup(self):
        self.add_input('geometry:wing_aspect_ratio', val=np.nan)

        self.add_output('oswald_coeff', val=np.nan)

    def compute(self, inputs, outputs):
        outputs['oswald_coeff'] = 1 / pi / 0.8 / inputs['geometry:wing_aspect_ratio']
