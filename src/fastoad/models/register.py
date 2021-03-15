"""
This module is for registering all internal OpenMDAO modules that we want
available through RegisterOpenMDAOSystem.

The choice is to have them declared in one place rather than having decorators
distributed along the code.
"""
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

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem
from .aerodynamics.aerodynamics_high_speed import AerodynamicsHighSpeed
from .aerodynamics.aerodynamics_landing import AerodynamicsLanding
from .aerodynamics.aerodynamics_low_speed import AerodynamicsLowSpeed
from .aerodynamics.aerodynamics_takeoff import AerodynamicsTakeoff
from .geometry import Geometry
from .handling_qualities.compute_static_margin import ComputeStaticMargin
from .handling_qualities.tail_sizing.compute_tail_areas import ComputeTailAreas
from .loops.compute_wing_area import ComputeWingArea
from .performances.mission.openmdao.link_mtow import ComputeMTOW
from .performances.mission.openmdao.mission import Mission
from .propulsion.fuel_propulsion.rubber_engine import OMRubberEngineComponent
from .propulsion.fuel_propulsion.rubber_engine.constants import RUBBER_ENGINE_DESCRIPTION
from .weight.weight import Weight

# Aerodynamics ################################################################
RegisterOpenMDAOSystem("fastoad.aerodynamics.takeoff.legacy", domain=ModelDomain.AERODYNAMICS)(
    AerodynamicsTakeoff
)
RegisterOpenMDAOSystem("fastoad.aerodynamics.landing.legacy", domain=ModelDomain.AERODYNAMICS)(
    AerodynamicsLanding
)
RegisterOpenMDAOSystem("fastoad.aerodynamics.highspeed.legacy", domain=ModelDomain.AERODYNAMICS,)(
    AerodynamicsHighSpeed
)
RegisterOpenMDAOSystem("fastoad.aerodynamics.lowspeed.legacy", domain=ModelDomain.AERODYNAMICS,)(
    AerodynamicsLowSpeed
)

# Geometry ####################################################################
RegisterOpenMDAOSystem("fastoad.geometry.legacy", domain=ModelDomain.GEOMETRY)(Geometry)

# handling qualities ##########################################################
RegisterOpenMDAOSystem(
    "fastoad.handling_qualities.tail_sizing", domain=ModelDomain.HANDLING_QUALITIES,
)(ComputeTailAreas)
RegisterOpenMDAOSystem(
    "fastoad.handling_qualities.static_margin", domain=ModelDomain.HANDLING_QUALITIES,
)(ComputeStaticMargin)

# Loops #######################################################################
RegisterOpenMDAOSystem("fastoad.loop.wing_area", domain=ModelDomain.OTHER)(ComputeWingArea)

RegisterOpenMDAOSystem("fastoad.mass_performances.compute_MTOW", domain=ModelDomain.OTHER)(
    ComputeMTOW
)

# Weight ######################################################################
RegisterOpenMDAOSystem("fastoad.weight.legacy", domain=ModelDomain.WEIGHT)(Weight)

# Performance #################################################################
RegisterOpenMDAOSystem("fastoad.performances.mission", domain=ModelDomain.PERFORMANCE)(Mission)

# Propulsion ##################################################################
RegisterOpenMDAOSystem(
    "fastoad.propulsion.rubber_engine",
    desc=RUBBER_ENGINE_DESCRIPTION,
    domain=ModelDomain.PROPULSION,
)(OMRubberEngineComponent)

# FIXME: for some reason, declaring here creates problems during tests when
#  restarting iPOPO framework, and it works better when the decorator actually
#  decorates the class.
# RegisterPropulsion("fastoad.wrapper.propulsion.rubber_engine", desc=RUBBER_ENGINE_DESCRIPTION,)(
#     OMRubberEngineWrapper
# )
