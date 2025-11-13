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
import scipy.constants as sc


def compute_fuel_mission(owe, payload, mission_range, tsfc, l_d, cruise_speed):
    """
    Computes the fuel consumed during the mission based on the Breguet's range equation

    :param owe: the structural mass, in kg
    :param payload: the payload mass, in kg
    :param mission_range: the mission range, in m
    :param tsfc: the thrust specific fuel consumption, in kg/N/s
    :param l_d: the lift-to-drag ratio in cruise conditions, no unit
    :param cruise_speed: Cruise speed, in m/s

    :return mission_fuel: the fuel consumed during the designated mission, in kg
    """

    # To simplify the computation, we will first start by computing the range parameter,
    # which correspond to the term inside the exponential in the original formula
    range_parameter = (mission_range * tsfc * sc.g) / (cruise_speed * l_d)

    # Let's now computed the fuel using Breguet's range equation rearranged
    mission_fuel = (owe + payload) * (np.exp(range_parameter) - 1.0)

    return mission_fuel
