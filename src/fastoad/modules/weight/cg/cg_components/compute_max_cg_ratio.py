"""
    Estimation of maximum center of gravity ratio
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
from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeMaxCGratio(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Maximum center of gravity ratio estimation """

    def setup(self):
        self.add_input('data:weight:aircraft:empty:CG:ratio', val=np.nan)
        self.add_input('data:weight:aircraft:load_case_1:CG:ratio', val=np.nan)
        self.add_input('data:weight:aircraft:load_case_2:CG:ratio', val=np.nan)
        self.add_input('data:weight:aircraft:load_case_3:CG:ratio', val=np.nan)
        self.add_input('data:weight:aircraft:load_case_4:CG:ratio', val=np.nan)

        self.add_output('data:weight:aircraft:CG:ratio')

        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        outputs['data:weight:aircraft:CG:ratio'] = max(
            inputs['data:weight:aircraft:empty:CG:ratio'],
            inputs['data:weight:aircraft:load_case_1:CG:ratio'],
            inputs['data:weight:aircraft:load_case_2:CG:ratio'],
            inputs['data:weight:aircraft:load_case_3:CG:ratio'],
            inputs['data:weight:aircraft:load_case_4:CG:ratio'])
