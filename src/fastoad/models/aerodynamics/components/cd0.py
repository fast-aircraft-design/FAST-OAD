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

import openmdao.api as om

from .cd0_fuselage import Cd0Fuselage
from .cd0_ht import Cd0HorizontalTail
from .cd0_nacelle_pylons import Cd0NacelleAndPylons
from .cd0_total import Cd0Total
from .cd0_vt import Cd0VerticalTail
from .cd0_wing import Cd0Wing


class CD0(om.Group):
    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.add_subsystem(
            "cd0_wing", Cd0Wing(low_speed_aero=self.options["low_speed_aero"]), promotes=["*"]
        )
        self.add_subsystem(
            "cd0_fuselage",
            Cd0Fuselage(low_speed_aero=self.options["low_speed_aero"]),
            promotes=["*"],
        )
        self.add_subsystem(
            "cd0_ht",
            Cd0HorizontalTail(low_speed_aero=self.options["low_speed_aero"]),
            promotes=["*"],
        )
        self.add_subsystem(
            "cd0_vt", Cd0VerticalTail(low_speed_aero=self.options["low_speed_aero"]), promotes=["*"]
        )
        self.add_subsystem(
            "cd0_nac_pylons",
            Cd0NacelleAndPylons(low_speed_aero=self.options["low_speed_aero"]),
            promotes=["*"],
        )
        self.add_subsystem(
            "cd0_total", Cd0Total(low_speed_aero=self.options["low_speed_aero"]), promotes=["*"]
        )
