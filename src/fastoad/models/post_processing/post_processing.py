"""Computation of the Altitude-Speed diagram."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from .speed_altitude_diagram import SpeedAltitudeDiagram
from .ceiling_mass_diagram import CeilingMassDiagram
from .available_power_diagram import AvailablepowerDiagram

import openmdao.api as om
import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("fastoad.postprocessing.belgian_legacy")
class PostProcessing(om.Group):
    def initialize(self):

        self.options.declare("propulsion_id", default="", types=str)

    def setup(self):

        self.add_subsystem(
            "speed_altitude",
            SpeedAltitudeDiagram(propulsion_id=self.options["propulsion_id"]),
            promotes=["*"],
        )
        self.add_subsystem(
            "ceiling_mass",
            CeilingMassDiagram(propulsion_id=self.options["propulsion_id"]),
            promotes=["*"],
        )
        self.add_subsystem(
            "available_power",
            AvailablepowerDiagram(propulsion_id=self.options["propulsion_id"]),
            promotes=["*"],
        )
