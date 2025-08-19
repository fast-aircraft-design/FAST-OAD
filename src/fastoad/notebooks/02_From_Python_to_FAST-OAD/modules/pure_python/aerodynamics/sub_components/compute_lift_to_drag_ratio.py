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

from fastoad.model_base.atmosphere import Atmosphere


def compute_l_d(cruise_altitude, cruise_speed, cd0, k, mtow, wing_area):
    """
    Computes the lift to drag ratio considering a lift equilibrium in cruise and a simple quadratic model

    :param cruise_altitude: Cruise altitude, in m
    :param cruise_speed: Cruise speed, in m/s
    :param cd0: Profile drag, no unit
    :param k: Lift induced drag coefficient, no unit
    :param mtow: Max Take-Off Weight, in kg
    :param wing_area: Wing area, in m2

    :return l_d: Lift-to-drag ratio in cruise conditions, no unit
    """

    # Air density at cruise level, to compute it, we will use the Atmosphere model available in
    # FAST-OAD, so we will create an Atmosphere instance using the cruise altitude and extract
    # its density attribute
    atm = Atmosphere(altitude=cruise_altitude, altitude_in_feet=False)
    rho = atm.density

    # Computation of the cruise lift coefficient using a simple equilibrium
    cl = (mtow * sc.g) / (0.5 * rho * cruise_speed**2.0 * wing_area)

    # Computation of the cruise drag coefficient using the simple quadratic model
    cd = cd0 + k * cl**2

    # Computation of the ratio
    l_d = cl / cd

    return l_d
