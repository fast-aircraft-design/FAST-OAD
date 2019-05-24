"""
Estimation of crew weight
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


class CrewWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ crew weight estimation (E) """

    def setup(self):
        self.add_input('cabin:PNT', val=np.nan)
        self.add_input('cabin:PNC', val=np.nan)

        self.add_output('weight_crew:E', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        cockpit_crew = inputs['cabin:PNT']
        cabin_crew = inputs['cabin:PNC']

        outputs['weight_crew:E'] = 85 * cockpit_crew + 75 * cabin_crew
