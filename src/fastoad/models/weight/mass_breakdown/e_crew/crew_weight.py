"""
Estimation of crew weight
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
        self.add_input("data:geometry:cabin:crew_count:technical", val=np.nan)
        self.add_input("data:geometry:cabin:crew_count:commercial", val=np.nan)

        self.add_output("data:weight:crew:mass", units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        cockpit_crew = inputs["data:geometry:cabin:crew_count:technical"]
        cabin_crew = inputs["data:geometry:cabin:crew_count:commercial"]

        outputs["data:weight:crew:mass"] = 85 * cockpit_crew + 75 * cabin_crew
