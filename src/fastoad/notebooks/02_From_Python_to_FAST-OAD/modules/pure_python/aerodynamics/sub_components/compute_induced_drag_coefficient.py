# This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
# Copyright (c) 2025 ONERA & ISAE-SUPAERO
# FAST-OAD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np


def compute_k(aspect_ratio):
    """
    Computes the induced drag coefficient based on the aspect ratio

    :param aspect_ratio: Wing aspect ratio, no unit

    :return k: induced drag coefficient, no unit
    """

    # Computation of the Oswald efficiency factor
    e = 1.78 * (1.0 - 0.045 * aspect_ratio**0.68) - 0.64

    # Computation of the lift induced drag coefficient
    k = 1.0 / (np.pi * aspect_ratio * e)

    return k
