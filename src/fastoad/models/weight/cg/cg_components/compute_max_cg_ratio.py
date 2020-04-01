"""
    Estimation of maximum center of gravity ratio
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


class ComputeMaxCGratio(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Maximum center of gravity ratio estimation """

    def setup(self):
        self.add_input("data:weight:aircraft:empty:CG:MAC_position", val=np.nan)
        self.add_input("data:weight:aircraft:load_case_1:CG:MAC_position", val=np.nan)
        self.add_input("data:weight:aircraft:load_case_2:CG:MAC_position", val=np.nan)
        self.add_input("data:weight:aircraft:load_case_3:CG:MAC_position", val=np.nan)
        self.add_input("data:weight:aircraft:load_case_4:CG:MAC_position", val=np.nan)
        self.add_input(
            "settings:weight:aircraft:CG:aft:MAC_position:margin",
            val=0.05,
            desc="Added margin for getting most aft CG position, "
            "as ratio of mean aerodynamic chord",
        )

        self.add_output("data:weight:aircraft:CG:aft:MAC_position")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        outputs["data:weight:aircraft:CG:aft:MAC_position"] = inputs[
            "settings:weight:aircraft:CG:aft:MAC_position:margin"
        ] + max(
            inputs["data:weight:aircraft:empty:CG:MAC_position"],
            inputs["data:weight:aircraft:load_case_1:CG:MAC_position"],
            inputs["data:weight:aircraft:load_case_2:CG:MAC_position"],
            inputs["data:weight:aircraft:load_case_3:CG:MAC_position"],
            inputs["data:weight:aircraft:load_case_4:CG:MAC_position"],
        )
