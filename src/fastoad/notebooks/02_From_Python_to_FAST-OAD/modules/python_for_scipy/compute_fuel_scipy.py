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

from ..pure_python.aerodynamics.aerodynamics import compute_aerodynamics
from ..pure_python.geometry.geometry import compute_geometry
from ..pure_python.mass.mass import compute_mass
from ..pure_python.performance.performance import compute_fuel_mission


def compute_fuel_scipy(
    x, wing_loading, cruise_altitude, cruise_speed, mission_range, payload, tsfc
):
    """
    Gather all the module main functions in the program main function that will compute the fuel consumed for the given
    MTOW

    :param x: Tuple containing the Old Max Take-Off Weight, in kg and the aspect ration with no unit
    :param wing_loading: Wing loading, in kg/m2
    :param cruise_speed: Cruise speed, in m/s
    :param cruise_altitude: Cruise altitude, in m
    :param payload: the payload mass, in kg
    :param mission_range: the mission range, in m
    :param tsfc: the thrust specific fuel consumption, in kg/N/s

    :return fuel_mission: Max Take-Off Weight computed based on the old value
    """

    # Let's unpack the tuple containing the two values that will be used for the optimization
    mtow = x[0]
    aspect_ratio = x[1]

    # Let's start by computing the aircraft geometry
    wing_area = compute_geometry(mtow=mtow, wing_loading=wing_loading)

    # Let's now compute its aerodynamic properties
    l_d = compute_aerodynamics(
        cruise_altitude=cruise_altitude,
        cruise_speed=cruise_speed,
        mtow=mtow,
        wing_area=wing_area,
        aspect_ratio=aspect_ratio,
    )

    # We can now compute its structural mass
    owe = compute_mass(mtow=mtow, wing_area=wing_area, aspect_ratio=aspect_ratio)

    # Let's now get the fuel consumed for the given mission
    fuel_mission = compute_fuel_mission(
        owe=owe,
        payload=payload,
        mission_range=mission_range,
        tsfc=tsfc,
        l_d=l_d,
        cruise_speed=cruise_speed,
    )

    return fuel_mission
