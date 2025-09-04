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


def update_mtow(owe, payload, mission_fuel):
    """
    Updates the MTOW based on the structural weight computed, the payload and the fuel consumed
    during the design mission.

    :param owe: the structural mass, in kg
    :param payload: the payload mass, in kg
    :param mission_fuel: the fuel consumed during the designated mission, in kg

    return mtow_new: the new Maximum Take-Off Weight based on the current iteration's computation,
    in kg
    """

    # Let's simply add the weight we computed
    mtow_new = owe + payload + mission_fuel

    return mtow_new
