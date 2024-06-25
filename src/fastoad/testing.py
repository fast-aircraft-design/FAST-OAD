"""Convenience utilities for testing."""
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

from typing import Union

import numpy as np
from openmdao import api as om
from openmdao.core.system import System

from fastoad.model_base.openmdao.group import BaseCycleGroup
from fastoad.openmdao.problem import FASTOADProblem
from fastoad.openmdao.variables import VariableList


def run_system(
    component: System, input_vars: Union[om.IndepVarComp, VariableList], **kwargs
) -> FASTOADProblem:
    """
    Runs and returns an OpenMDAO problem with provided component and data.

    An error is raised if at least one variable has NaN value despite provided values in
    input_vars. The raised error lists the identified variables.

    :param component: OpenMDAO component to be run
    :param input_vars: input data for the component
    :param kwargs: options of :class:`fastoad.api.BaseCycleGroup`, to add control solvers
                   in the problem
    :return: a FASTOADProblem instance
    """

    if isinstance(component, om.ImplicitComponent) and "nonlinear_solver" not in kwargs:
        kwargs["nonlinear_solver"] = "om.NewtonSolver"
        kwargs["linear_solver"] = "om.DirectSolver"

        if kwargs.get("nonlinear_solver_options", {}).get("solve_subsystems") is None:
            kwargs["nonlinear_solver_options"]["solve_subsystems"] = False

    problem = om.Problem()
    model = problem.model = BaseCycleGroup(**kwargs)

    if isinstance(input_vars, VariableList):
        input_vars = input_vars.to_ivc()

    model.add_subsystem("inputs", input_vars, promotes=["*"])
    model.add_subsystem("component", component, promotes=["*"])

    problem.setup()
    variable_names = [
        var.name
        for var in VariableList.from_problem(problem, io_status="inputs")
        if np.any(np.isnan(var.val))
    ]

    assert not variable_names, "These inputs are not provided: %s" % variable_names

    problem.run_model()

    return problem
