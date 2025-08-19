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


def compute_wing_area(mtow, wing_loading):
    """
    Computes the wing area based on the provided MTOW and wing loading

    :param mtow: Max Take-Off Weight, in kg
    :param wing_loading: Wing loading, in kg/m2

    :return wing_area: Wing area, in m2
    """

    # Computation of the wing area
    wing_area = mtow / wing_loading

    return wing_area
