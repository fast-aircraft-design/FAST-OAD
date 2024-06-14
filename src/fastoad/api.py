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

# pylint: disable=unused-import
# flake8: noqa

# The comment below prevents PyCharm from "optimizing" (i.e. removing) these imports.
# noinspection PyUnresolvedReferences
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

# noinspection PyUnresolvedReferences
from fastoad.gui.analysis_and_plots import (
    aircraft_geometry_plot,
    drag_polar_plot,
    mass_breakdown_bar_plot,
    mass_breakdown_sun_plot,
    payload_range_plot,
    wing_geometry_plot,
)

# noinspection PyUnresolvedReferences
from fastoad.gui.mission_viewer import MissionViewer

# noinspection PyUnresolvedReferences
from fastoad.gui.optimization_viewer import OptimizationViewer

# noinspection PyUnresolvedReferences
from fastoad.gui.variable_viewer import VariableViewer

# noinspection PyUnresolvedReferences
from fastoad.io import DataFile

# noinspection PyUnresolvedReferences
from fastoad.io.configuration import FASTOADProblemConfigurator

# noinspection PyUnresolvedReferences
from fastoad.model_base import Atmosphere, AtmosphereSI, FlightPoint

# noinspection PyUnresolvedReferences
from fastoad.model_base.datacls import MANDATORY_FIELD

# noinspection PyUnresolvedReferences
from fastoad.model_base.openmdao.group import CycleGroup, BaseCycleGroup

# noinspection PyUnresolvedReferences
from fastoad.model_base.propulsion import IOMPropulsionWrapper

# noinspection PyUnresolvedReferences
from fastoad.models.performances.mission.segments.base import (
    AbstractFlightSegment,
    IFlightPart,
    RegisterSegment,
)

# noinspection PyUnresolvedReferences
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

# noinspection PyUnresolvedReferences
from fastoad.module_management.service_registry import (
    RegisterOpenMDAOSystem,
    RegisterPropulsion,
    RegisterSpecializedService,
    RegisterSubmodel,
)

# noinspection PyUnresolvedReferences
from fastoad.openmdao.problem import FASTOADProblem

# noinspection PyUnresolvedReferences
from fastoad.openmdao.validity_checker import ValidityDomainChecker

# noinspection PyUnresolvedReferences
from fastoad.openmdao.variables import Variable, VariableList
