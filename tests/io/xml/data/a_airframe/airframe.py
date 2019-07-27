"""
Total Aiframe Group
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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
from openmdao.core.group import Group

from fastoad.modules.mass_breakdown.a_airframe import WingWeight, FuselageWeight, EmpennageWeight, \
    FlightControlsWeight, LandingGearWeight, PylonsWeight, PaintWeight

class Airframe(Group):
    """ Airframe weight estimation

    This group aggregates weight from all components of the airframe.
    """

    def setup(self):
        # Airframe
        self.add_subsystem('wing_weight', WingWeight(), promotes=['*'])
        self.add_subsystem('fuselage_weight', FuselageWeight(), promotes=['*'])
        self.add_subsystem('empennage_weight', EmpennageWeight(), promotes=['*'])
        self.add_subsystem('flight_controls_weight', FlightControlsWeight(), promotes=['*'])
        self.add_subsystem('landing_gear_weight', LandingGearWeight(), promotes=['*'])
        self.add_subsystem('pylons_weight', PylonsWeight(), promotes=['*'])
        self.add_subsystem('paint_weight', PaintWeight(), promotes=['*'])