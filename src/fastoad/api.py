"""This module gathers key FAST-OAD classes and functions for convenient import."""
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

# pylint: disable=unused-import
# flake8: noqa


from fastoad.cmd.api import (
    evaluate_problem,
    generate_configuration_file,
    generate_inputs,
    list_modules,
    list_variables,
    optimization_viewer,
    optimize_problem,
    variable_viewer,
    write_n2,
    write_xdsm,
)

from fastoad.io.configuration import FASTOADProblemConfigurator
from fastoad.openmdao.problem import FASTOADProblem

from fastoad.io import DataFile
from fastoad.openmdao.variables import Variable, VariableList

from fastoad.model_base import Atmosphere, AtmosphereSI, FlightPoint

from fastoad.module_management.service_registry import (
    RegisterOpenMDAOSystem,
    RegisterPropulsion,
    RegisterSpecializedService,
    RegisterSubmodel,
)
from fastoad.model_base.propulsion import IOMPropulsionWrapper
from fastoad.openmdao.validity_checker import ValidityDomainChecker

from fastoad.gui.mission_viewer import MissionViewer
from fastoad.gui.optimization_viewer import OptimizationViewer
from fastoad.gui.variable_viewer import VariableViewer
from fastoad.gui.analysis_and_plots import (
    aircraft_geometry_plot,
    drag_polar_plot,
    mass_breakdown_bar_plot,
    mass_breakdown_sun_plot,
    wing_geometry_plot,
)
