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


def compute_cd0(wing_area):
    """
    Computes the profile drag of the aircraft based on the wing area

    :param wing_area: Wing area, in m2

    :return cd0: profile drag, no unit
    """

    # Wet area of the aircraft without the wings
    wing_area_ref = 13.50

    # Profile drag coefficient of the aircraft without the wings
    cd0_other = 0.022

    # Constant linking the wing profile drag to its wet area, and by extension, its reference area
    c = 0.0004

    # Computation of the profile drag
    cd0 = cd0_other * wing_area_ref / wing_area + c

    return cd0
