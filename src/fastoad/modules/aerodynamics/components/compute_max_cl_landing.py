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
from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeMaxClLanding(ExplicitComponent):
    def setup(self):
        self.add_input('aerodynamics:Cl_max_clean', val=np.nan)
        self.add_input('delta_cl_landing', val=np.nan)
        self.add_input('kfactors_aero:K_HL_LDG', val=np.nan)
        self.add_output('aerodynamics:Cl_max_landing', val=np.nan)

    def compute(self, inputs, outputs):
        cl_max_clean = inputs['aerodynamics:Cl_max_clean']
        cl_max_landing = cl_max_clean + inputs['delta_cl_landing']
        cl_max_landing = cl_max_landing * inputs['kfactors_aero:K_HL_LDG']

        outputs['aerodynamics:Cl_max_landing'] = cl_max_landing
