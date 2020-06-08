"""
Convenience functions for helping tests
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
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

import logging

import openmdao.api as om
from fastoad.openmdao.types import SystemSubclass
from fastoad.openmdao.utils import get_unconnected_input_names

# Logger for this module
_LOGGER = logging.getLogger(__name__)


def run_system(
    component: SystemSubclass, input_vars: om.IndepVarComp, setup_mode="auto", add_solvers=False
):
    """ Runs and returns an OpenMDAO problem with provided component and data"""
    problem = om.Problem()
    model = problem.model
    model.add_subsystem("inputs", input_vars, promotes=["*"])
    model.add_subsystem("component", component, promotes=["*"])
    if add_solvers:
        model.nonlinear_solver = om.NewtonSolver(solve_subsystems=False)
        model.linear_solver = om.DirectSolver()

    problem.setup(mode=setup_mode)
    missing, _ = get_unconnected_input_names(problem, _LOGGER)
    assert not missing, "These inputs are not provided: %s" % missing

    problem.run_model()

    return problem
