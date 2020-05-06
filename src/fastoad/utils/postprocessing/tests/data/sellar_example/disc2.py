# -*- coding: utf-8 -*-
"""
    Sellar discipline 2
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
from .disc2_base import Disc2Base


class Disc2(Disc2Base):
    """ An OpenMDAO component to encapsulate Disc2 discipline """

    # pylint: disable=invalid-name
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """
        Evaluates the equation
        y2 = y1**(.5) + z1 + z2
        """

        z1 = inputs["z"][0]
        z2 = inputs["z"][1]
        y1 = inputs["y1"]

        # Note: this may cause some issues. However, y1 is constrained to be
        # above 3.16, so lets just let it converge, and the optimizer will
        # throw it out
        if y1.real < 0.0:
            y1 *= -1

        outputs["y2"] = y1 ** 0.5 + z1 + z2
