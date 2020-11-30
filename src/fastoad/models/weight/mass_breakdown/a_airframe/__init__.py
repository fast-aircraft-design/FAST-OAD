"""
Estimation of airframe weight
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
from .a1_wing_weight import WingWeight  # A1
from .a2_fuselage_weight import FuselageWeight  # A2
from .a3_empennage_weight import EmpennageWeight  # A3
from .a4_flight_control_weight import FlightControlsWeight  # A4
from .a5_landing_gear_weight import LandingGearWeight  # A5
from .a6_pylons_weight import PylonsWeight  # A6
from .a7_paint_weight import PaintWeight  # A7
