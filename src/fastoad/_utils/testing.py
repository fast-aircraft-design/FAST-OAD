"""
Convenience functions for helping tests
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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
from openmdao.core.system import System

from fastoad.openmdao.variables import VariableList

_LOGGER = logging.getLogger(__name__)  # Logger for this module


def run_system(
    component: System, input_vars: om.IndepVarComp, setup_mode="auto", add_solvers=False
):
    """Runs and returns an OpenMDAO problem with provided component and data"""
    problem = om.Problem()
    model = problem.model
    model.add_subsystem("inputs", input_vars, promotes=["*"])
    model.add_subsystem("component", component, promotes=["*"])
    if add_solvers:
        model.nonlinear_solver = om.NewtonSolver(solve_subsystems=False)
        model.linear_solver = om.DirectSolver()

    problem.setup(mode=setup_mode)
    variables = VariableList.from_unconnected_inputs(problem)
    assert not variables, "These inputs are not provided: %s" % variables.names()

    problem.run_model()

    return problem
