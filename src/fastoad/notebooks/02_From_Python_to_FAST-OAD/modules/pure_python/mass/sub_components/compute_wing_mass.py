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

import scipy.constants as sc


def compute_wing_mass(mtow, aspect_ratio, wing_area):
    """
    Computes the wing mass based on the MTOW, its area and aspect ratio

    :param wing_area: Wing area, in m2
    :param aspect_ratio: Wing aspect ratio, no unit
    :param mtow: Max Take-Off Weight, in kg

    :return wing mass: the wing_mass, in kg
    """

    # Let's start by converting the quantities in imperial units
    mtow_lbm = mtow / sc.lb
    wing_area_ft2 = wing_area / sc.foot**2.0

    # Let's now apply the formula
    wing_mass_lbm = (
        96.948
        * (
            (5.7 * mtow_lbm / 1.0e5) ** 0.65
            * aspect_ratio**0.57
            * (wing_area_ft2 / 100.0) ** 0.61
            * 2.5
        )
        ** 0.993
    )

    # Converting wing mass in kg
    wing_mass = wing_mass_lbm * sc.lb

    return wing_mass
