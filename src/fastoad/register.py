"""
This module is for registering all internal OpenMDAO modules that we want
available through RegisterOpenMDAOSystem
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

from fastoad.models.aerodynamics.aerodynamics_high_speed import AerodynamicsHighSpeed
from fastoad.models.aerodynamics.aerodynamics_landing import AerodynamicsLanding
from fastoad.models.aerodynamics.aerodynamics_low_speed import AerodynamicsLowSpeed
from fastoad.models.aerodynamics.aerodynamics_takeoff import AerodynamicsTakeoff
from fastoad.models.geometry import Geometry
from fastoad.models.handling_qualities.compute_static_margin import ComputeStaticMargin
from fastoad.models.handling_qualities.tail_sizing.compute_tail_areas import ComputeTailAreas
from fastoad.models.loops.compute_wing_area import ComputeWingArea
from fastoad.models.performances.breguet import OMBreguet
from fastoad.models.performances.mission.openmdao.sizing_mission import SizingMission
from fastoad.models.propulsion.fuel_propulsion.rubber_engine import (
    OMRubberEngineComponent,
    OMRubberEngineWrapper,
)
from fastoad.models.weight.mass_breakdown.mass_breakdown import MTOWComputation
from fastoad.models.weight.weight import Weight
from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterPropulsion, RegisterOpenMDAOSystem


def register_openmdao_systems():
    """
    The place where to register FAST-OAD internal models.

    Warning: this function is effective only if called from a Python module that
    is a started bundle for iPOPO
    """
    # Aerodynamics ################################################################
    RegisterOpenMDAOSystem("fastoad.aerodynamics.takeoff.legacy", domain=ModelDomain.AERODYNAMICS)(
        AerodynamicsTakeoff
    )
    RegisterOpenMDAOSystem("fastoad.aerodynamics.landing.legacy", domain=ModelDomain.AERODYNAMICS)(
        AerodynamicsLanding
    )
    RegisterOpenMDAOSystem(
        "fastoad.aerodynamics.highspeed.legacy", domain=ModelDomain.AERODYNAMICS,
    )(AerodynamicsHighSpeed)
    RegisterOpenMDAOSystem(
        "fastoad.aerodynamics.lowspeed.legacy", domain=ModelDomain.AERODYNAMICS,
    )(AerodynamicsLowSpeed)

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

    RegisterOpenMDAOSystem("fastoad.loop.mtow", domain=ModelDomain.WEIGHT)(MTOWComputation)

    # Weight ######################################################################
    RegisterOpenMDAOSystem("fastoad.weight.legacy", domain=ModelDomain.WEIGHT)(Weight)
    # Performance #################################################################
    RegisterOpenMDAOSystem("fastoad.performances.breguet", domain=ModelDomain.PERFORMANCE)(
        OMBreguet
    )

    RegisterOpenMDAOSystem("fastoad.performances.sizing_mission", domain=ModelDomain.PERFORMANCE)(
        SizingMission
    )

    # Propulsion ##################################################################
    rubber_engine_description = """
    Parametric engine model as OpenMDAO component.
    
    Implementation of E. Roux models for fuel consumption of low bypass ratio engines
    For more information, see RubberEngine class in FAST-OAD developer documentation.
    """

    RegisterOpenMDAOSystem(
        "fastoad.propulsion.rubber_engine",
        desc=rubber_engine_description,
        domain=ModelDomain.PROPULSION,
    )(OMRubberEngineComponent)

    RegisterPropulsion("fastoad.wrapper.propulsion.rubber_engine", desc=rubber_engine_description,)(
        OMRubberEngineWrapper
    )
