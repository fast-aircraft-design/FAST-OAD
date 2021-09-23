"""
    Estimation of center of gravity for load case 2
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from fastoad.models.weight.cg.cg_components.compute_cg_loadcase import AbstractComputeCGLoadCase


class ComputeCGLoadCase2(AbstractComputeCGLoadCase):
    # TODO: Document equations. Cite sources
    """ Center of gravity estimation for load case 3 """

    def setup(self):
        self.options["case_number"] = 2
        self.add_input("data:weight:aircraft:MFW", val=np.nan, units="kg")
        self.add_input("data:weight:fuel_tank:CG:x", val=np.nan, units="m")
        return super().setup()

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        outputs[self.output_name] = self.compute_cg_ratio(
            inputs,
            weight_per_pax=90.0,
            weight_front_fret=inputs["data:TLAR:NPAX"] * 20.0,
            weight_rear_fret=inputs["data:TLAR:NPAX"] * 20.0,
            weight_fuel=inputs["data:weight:aircraft:MFW"],
            cg_fuel=inputs["data:weight:fuel_tank:CG:x"],
        )
