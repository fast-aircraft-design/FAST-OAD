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

from .sub_components.compute_induced_drag_coefficient import compute_k
from .sub_components.compute_lift_to_drag_ratio import compute_l_d
from .sub_components.compute_profile_drag import compute_cd0


def compute_aerodynamics(cruise_altitude, cruise_speed, mtow, wing_area, aspect_ratio):
    """
    Gather all the aerodynamics sub-functions in the main function

    :param cruise_altitude: Cruise altitude, in m
    :param cruise_speed: Cruise speed, in m/s
    :param mtow: Max Take-Off Weight, in kg
    :param wing_area: Wing area; in m2
    :param aspect_ratio: Wing aspect ratio, no unit

    :return wing_area: Wing area, in m2
    """

    # Let's start by computing the profile drag coefficient
    cd0 = compute_cd0(wing_area=wing_area)

    # Let's now compute the lift induced drag coefficient
    k = compute_k(aspect_ratio=aspect_ratio)

    # We can now compute the lift-to-drag ratio
    l_d = compute_l_d(
        cruise_altitude=cruise_altitude,
        cruise_speed=cruise_speed,
        cd0=cd0,
        k=k,
        mtow=mtow,
        wing_area=wing_area,
    )

    return l_d
