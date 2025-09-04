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

from .sub_components.compute_fuel_mass import compute_fuel_mission


def compute_performance(owe, payload, mission_range, tsfc, l_d, cruise_speed):
    """
    Gather all the performances sub-functions in the main function

    :param owe: the structural mass, in kg
    :param payload: the payload mass, in kg
    :param mission_range: the mission range, in m
    :param tsfc: the thrust specific fuel consumption, in kg/N/s
    :param l_d: the lift-to-drag ratio in cruise conditions, no unit
    :param cruise_speed: Cruise speed, in m/s

    :return mission_fuel: the fuel consumed during the designated mission, in kg
    """

    # Let's start by computing the fuel consumed during the mission
    mission_fuel = compute_fuel_mission(
        owe=owe,
        payload=payload,
        mission_range=mission_range,
        tsfc=tsfc,
        l_d=l_d,
        cruise_speed=cruise_speed,
    )

    return mission_fuel
