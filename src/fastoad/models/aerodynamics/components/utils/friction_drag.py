"""Computation of friction drag."""
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


def get_flat_plate_friction_drag_coefficient(length, mach, reynolds):
    """

    :param length: flat plate length in meters
    :param mach: Mach number
    :param reynolds: Reynolds number
    :return: Drag coefficient w.r.t. a surface of area length*1 m**2
    """
    c_f = 0.455 / ((1 + 0.144 * mach ** 2) ** 0.65 * (np.log10(reynolds * length)) ** 2.58)
    return c_f
