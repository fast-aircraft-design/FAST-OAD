"""
Classes for simulating flight segments.

Be sure to import this package before interpreting a mission input file.
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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

# pylint: disable=unused-import
# flake8: noqa

# With these imports, importing only the current package ensures to have all
# these segments available when interpreting a mission input file
from . import (
    altitude_change,
    cruise,
    ground_speed_change,
    hold,
    mass_input,
    speed_change,
    start,
    takeoff,
    taxi,
    transition,
)
