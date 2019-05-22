"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

#      This file is part of FAST : A framework for rapid Overall Aircraft Design
#      Copyright (C) 2019  ONERA/ISAE
#      FAST is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class UpdateMLWandMZFW(ExplicitComponent):

    def setup(self):
        self.add_input('weight:OEW', val=np.nan)
        self.add_input('weight:Max_PL', val=np.nan)

        self.add_output('weight:MZFW')
        self.add_output('weight:MLW')

    def compute(self, inputs, outputs):
        oew = inputs['weight:OEW'][0]
        max_pl = inputs['weight:Max_PL'][0]
        mzfw = oew + max_pl
        mlw = 1.06 * mzfw

        outputs['weight:MZFW'] = mzfw
        outputs['weight:MLW'] = mlw
