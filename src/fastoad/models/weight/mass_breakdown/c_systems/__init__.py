"""
Estimation of weight of all-mission systems
"""

#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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

from .c1_power_systems_weight import PowerSystemsWeight
from .c2_life_support_systems_weight import LifeSupportSystemsWeight
from .c3_navigation_systems_weight import NavigationSystemsWeight
from .c4_transmissions_systems_weight import TransmissionSystemsWeight
from .c5_fixed_operational_systems_weight import FixedOperationalSystemsWeight
from .c6_flight_kit_weight import FlightKitWeight
