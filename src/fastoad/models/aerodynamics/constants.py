"""Constants for aerodynamics models."""
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

from aenum import Enum

POLAR_POINT_COUNT = 150

SERVICE_OSWALD_COEFFICIENT = "service.aerodynamics.oswald_coefficient"
SERVICE_INDUCED_DRAG_COEFFICIENT = "service.aerodynamics.induced_drag_coefficient"
SERVICE_REYNOLDS_COEFFICIENT = "service.aerodynamics.reynolds_coefficient"
SERVICE_INITIALIZE_CL = "service.aerodynamics.initialize_CL"
SERVICE_CD0 = "service.aerodynamics.CD0"
SERVICE_CD0_WING = "service.aerodynamics.CD0.wing"
SERVICE_CD0_FUSELAGE = "service.aerodynamics.CD0.fuselage"
SERVICE_CD0_HORIZONTAL_TAIL = "service.aerodynamics.CD0.horizontal_tail"
SERVICE_CD0_VERTICAL_TAIL = "service.aerodynamics.CD0.vertical_tail"
SERVICE_CD0_NACELLES_PYLONS = "service.aerodynamics.CD0.nacelles_pylons"
SERVICE_CD0_SUM = "service.aerodynamics.CD0.sum"
SERVICE_CD_COMPRESSIBILITY = "service.aerodynamics.CD.compressibility"
SERVICE_CD_TRIM = "service.aerodynamics.CD.trim"
SERVICE_POLAR = "service.aerodynamics.polar"
SERVICE_HIGH_LIFT = "service.aerodynamics.high_lift"
SERVICE_XFOIL = "service.aerodynamics.xfoil"
SERVICE_LANDING_MAX_CL_CLEAN = "service.aerodynamics.landing.max_CL_clean"
SERVICE_LANDING_MAX_CL = "service.aerodynamics.landing.max_CL"
SERVICE_LANDING_MACH_REYNOLDS = "service.aerodynamics.landing.mach_reynolds"
SERVICE_LOW_SPEED_CL_AOA = "service.aerodynamics.low_speed.CL_AoA"


class PolarType(Enum):
    """Enumeration of polar types to be computed."""

    HIGH_SPEED = "high_speed"
    LOW_SPEED = "low_speed"
    TAKEOFF = "takeoff"
    LANDING = "landing"
