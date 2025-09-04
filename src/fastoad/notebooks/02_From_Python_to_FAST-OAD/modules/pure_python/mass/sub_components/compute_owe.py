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


def compute_owe(wing_mass, mtow):
    """
    Computes the aircraft structural mass based on its MTOW and wing mass

    :param wing_mass: Wing mass, in kg
    :param mtow: Max Take-Off Weight, in kg

    :return owe: the structural mass, in kg
    """

    # Let's start by computing the weight of the aircraft without the wings
    owe_without_wing = mtow * (0.43 + 0.0066 * np.log(mtow))

    # Let's now add the wing mass to get the structural weight
    owe = owe_without_wing + wing_mass

    return owe
