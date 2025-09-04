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
import openmdao.api as om
import scipy.constants as sc

from fastoad.model_base import Atmosphere


class ComputeLiftToDragRatio(om.ExplicitComponent):
    """
    Computes the lift to drag ratio considering a lift equilibrium in cruise and a simple
    quadratic model.
    """

    def setup(self):
        # Defining the input(s)

        self.add_input(
            name="cruise_altitude", units="m", val=np.nan
        )  # For a float or int, shape don't have to be
        # provided
        self.add_input(name="cruise_speed", units="m/s", val=np.nan)
        self.add_input(
            name="profile_drag_coefficient", val=np.nan
        )  # When the quantity does not have a unit, the units
        # field doesn't need to be filled
        self.add_input(name="induced_drag_coefficient", val=np.nan)
        self.add_input(name="mtow", units="kg", val=np.nan)
        self.add_input(
            name="wing_area", units="m**2", val=np.nan
        )  # OpenMDAO understands the multiplication/division
        # of units in between them hence why the m**2 is understood

        # Defining the output(s)

        self.add_output(name="l_d_ratio")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        # Assigning the input to local variable for clarity
        cruise_altitude = inputs["cruise_altitude"]
        cruise_speed = inputs["cruise_speed"]
        cd0 = inputs["profile_drag_coefficient"]
        k = inputs["induced_drag_coefficient"]
        mtow = inputs["mtow"]
        wing_area = inputs["wing_area"]

        # Air density at sea-level, to compute it, we will use the Atmosphere
        # model available in FAST-OAD, so we will create an Atmosphere instance
        # using the cruise altitude and extract its density attribute
        atm = Atmosphere(altitude=cruise_altitude, altitude_in_feet=False)
        rho = atm.density

        # Computation of the cruise lift coefficient using a simple equilibrium
        cl = (mtow * sc.g) / (0.5 * rho * cruise_speed**2.0 * wing_area)

        # Computation of the cruise drag coefficient using the simple quadratic model
        cd = cd0 + k * cl**2

        # Computation of the ratio
        l_d = cl / cd

        outputs["l_d_ratio"] = l_d
