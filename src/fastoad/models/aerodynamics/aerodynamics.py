"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from fastoad.models.aerodynamics.aerodynamics_high_speed import AerodynamicsHighSpeed
from fastoad.models.aerodynamics.aerodynamics_landing import AerodynamicsLanding
from fastoad.models.aerodynamics.aerodynamics_low_speed import AerodynamicsLowSpeed
from openmdao.api import Group


class Aerodynamics(Group):
    def setup(self):
        # Compute the low speed aero (Cl alpha at takeoff and Cl0)
        self.add_subsystem("aero_low", AerodynamicsLowSpeed(), promotes=["*"])

        # Compute CL max landing
        self.add_subsystem("aero_landing", AerodynamicsLanding(), promotes=["*"])

        # Compute cruise characteristics
        self.add_subsystem("aero_high", AerodynamicsHighSpeed(), promotes=["*"])
