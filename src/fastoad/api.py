"""This module gathers key FAST-OAD classes and functions for convenient import."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

from fastoad import __version__
from fastoad.cmd.api import (
    evaluate_problem,
    generate_configuration_file,
    generate_inputs,
    generate_notebooks,
    generate_source_data_file,
    get_plugin_information,
    list_modules,
    list_variables,
    optimization_viewer,
    optimize_problem,
    variable_viewer,
    write_n2,
    write_xdsm,
)
from fastoad.cmd.calc_runner import CalcRunner
from fastoad.gui.analysis_and_plots import (
    aircraft_geometry_plot,
    drag_polar_plot,
    mass_breakdown_bar_plot,
    mass_breakdown_sun_plot,
    payload_range_plot,
    wing_geometry_plot,
)
from fastoad.gui.mission_viewer import MissionViewer
from fastoad.gui.optimization_viewer import OptimizationViewer
from fastoad.gui.variable_viewer import VariableViewer
from fastoad.io import DataFile
from fastoad.io.configuration import FASTOADProblemConfigurator
from fastoad.model_base import Atmosphere, AtmosphereSI, FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from fastoad.model_base.openmdao.group import BaseCycleGroup, CycleGroup
from fastoad.model_base.propulsion import IOMPropulsionWrapper
from fastoad.models.performances.mission.segments.base import (
    AbstractFlightSegment,
    IFlightPart,
    RegisterSegment,
)
from fastoad.models.performances.mission.segments.time_step_base import (
    AbstractFixedDurationSegment,
    AbstractGroundSegment,
    AbstractManualThrustSegment,
    AbstractPolarModifier,
    AbstractRegulatedThrustSegment,
    AbstractTakeOffSegment,
    AbstractTimeStepFlightSegment,
    FlightSegment,
)
from fastoad.module_management.service_registry import (
    RegisterOpenMDAOSystem,
    RegisterPropulsion,
    RegisterSpecializedService,
    RegisterSubmodel,
)
from fastoad.openmdao.problem import FASTOADProblem
from fastoad.openmdao.validity_checker import ValidityDomainChecker
from fastoad.openmdao.variables import Variable, VariableList

__all__ = [
    "__version__",
    "evaluate_problem",
    "generate_configuration_file",
    "generate_inputs",
    "generate_notebooks",
    "generate_source_data_file",
    "get_plugin_information",
    "list_modules",
    "list_variables",
    "optimization_viewer",
    "optimize_problem",
    "variable_viewer",
    "write_n2",
    "write_xdsm",
    "CalcRunner",
    "aircraft_geometry_plot",
    "drag_polar_plot",
    "mass_breakdown_bar_plot",
    "mass_breakdown_sun_plot",
    "payload_range_plot",
    "wing_geometry_plot",
    "MissionViewer",
    "OptimizationViewer",
    "VariableViewer",
    "DataFile",
    "FASTOADProblemConfigurator",
    "Atmosphere",
    "AtmosphereSI",
    "FlightPoint",
    "MANDATORY_FIELD",
    "BaseCycleGroup",
    "CycleGroup",
    "IOMPropulsionWrapper",
    "AbstractFlightSegment",
    "IFlightPart",
    "RegisterSegment",
    "AbstractFixedDurationSegment",
    "AbstractGroundSegment",
    "AbstractManualThrustSegment",
    "AbstractPolarModifier",
    "AbstractRegulatedThrustSegment",
    "AbstractTakeOffSegment",
    "AbstractTimeStepFlightSegment",
    "FlightSegment",
    "RegisterOpenMDAOSystem",
    "RegisterPropulsion",
    "RegisterSpecializedService",
    "RegisterSubmodel",
    "FASTOADProblem",
    "ValidityDomainChecker",
    "Variable",
    "VariableList",
]
