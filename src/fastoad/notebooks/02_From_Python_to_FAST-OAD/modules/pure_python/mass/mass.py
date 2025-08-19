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

from .sub_components.compute_owe import compute_owe
from .sub_components.compute_wing_mass import compute_wing_mass


def compute_mass(mtow, wing_area, aspect_ratio):
    """
    Gather all the mass sub-functions in the main function

    :param mtow: Max Take-Off Weight, in kg
    :param wing_area: Wing area, in m2
    :param aspect_ratio: Wing aspect ratio, no unit

    :return owe: the structural mass, in kg
    """

    # Let's start by computing the wing mass
    wing_mass = compute_wing_mass(mtow=mtow, aspect_ratio=aspect_ratio, wing_area=wing_area)

    # Let's now compute the owe
    owe = compute_owe(
        wing_mass=wing_mass,
        mtow=mtow,
    )

    return owe
