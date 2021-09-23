"""
    Estimation of center of gravity for load case 1
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

from .compute_cg_loadcase import ComputeCGLoadCase


class ComputeCGLoadCase1(ComputeCGLoadCase):
    """ Center of gravity estimation for load case 1 """

    def setup(self):
        self.options["case_number"] = 1
        self.options["weight_per_pax"] = 80.0
        self.options["weight_front_fret_per_pax"] = 0.0
        self.options["weight_rear_fret_per_pax"] = 0.0
        return super().setup()
