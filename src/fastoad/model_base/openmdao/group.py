"""
Convenience classes to be used in OpenMDAO components
"""
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

from typing import Type

import openmdao.api as om
from openmdao.solvers.solver import Solver


class CycleGroup(om.Group):
    """
    Use this class as a base class if your model should contain a NonlinearBlockGS solver.

    This class defines standard options to control the solvers.

    Please be sure to call the `super()` method when using initialize() and setup()
    in the derived class.

    By default, the inner solver is activated. If you want your subclass to deactivate
    the solver by default, you can define it when subclassing::

        class MyGroup(CycleGroup, use_solver_by_default=False):
            ...

    You may also specify, for your subclass, default solver settings that will be used when adding
    the solvers, unless overwritten through by OpenMDAO options when instantiating::

        class MyGroup(
            CycleGroup,
            default_nonlinear_options={"maxiter": 50, "iprint": 0},
            default_linear_options={"maxiter": 100},
        ):
            ...

    """

    def __init_subclass__(
        cls,
        use_solver_by_default: bool = True,
        default_nonlinear_options: dict = None,
        default_linear_options: dict = None,
    ):
        cls.use_solver_by_default = use_solver_by_default
        cls.default_solver_options = {
            "nonlinear_options": default_nonlinear_options if default_nonlinear_options else {},
            "linear_options": default_linear_options if default_linear_options else {},
        }

    def initialize(self):
        super().initialize()
        self.options.declare(
            "nonlinear_solver",
            types=(bool, str),
            default=True,
            desc="If True, a NonlinearBlockGS solver is added to the group. "
            "If a string is given like 'om.NewtonSolver', it will be used.",
        ),
        self.options.declare(
            "linear_solver",
            types=(bool, str),
            default=True,
            desc="If True, a DirectSolver is added to the group."
            "If a string is given like 'om.LinearBlockGS', it will be used.",
        )
        self.options.declare(
            "use_inner_solver",
            types=bool,
            default=True,
            desc="If True, a NonlinearBlockGS solver and a linear DirectSolver "
            "are added to the group.",
            deprecation="Please use options 'non_linear_solver' and 'linear_solver'",
        )
        self.options.declare(
            "nonlinear_options",
            types=dict,
            default={},
            desc="options for non-linear solver. Ignored if use_inner_solver is False.",
        )
        self.options.declare(
            "linear_options",
            types=dict,
            default={},
            desc="options for linear solver. Ignored if use_inner_solver is False.",
        )

    def setup(self):
        linear_solver_class = self._get_solver_class("linear_solver", om.DirectSolver)
        nonlinear_solver_class = self._get_solver_class("nonlinear_solver", om.NonlinearBlockGS)

        for solver, solver_options in self.default_solver_options.items():
            for key, value in solver_options.items():
                self.options[solver][key] = self.options[solver].get(key, value)

        linear_options = self._get_solver_options("linear_options")
        nonlinear_options = self._get_solver_options("nonlinear_options")

        if linear_solver_class:
            self.linear_solver = linear_solver_class(**linear_options)
        if nonlinear_solver_class:
            self.nonlinear_solver = nonlinear_solver_class(**nonlinear_options)

        super().setup()

    def _get_solver_class(self, option_name: str, default_solver: Type[Solver]):
        if isinstance(self.options[option_name], str):
            solver_class = eval(self.options[option_name], {"__builtins__": {}}, {"om": om})
        elif self.options[option_name] or self.options["use_inner_solver"]:
            solver_class = default_solver
        else:
            solver_class = None
        return solver_class

    def _get_solver_options(self, openmdao_option_name: str):
        solver_options = self.default_solver_options[openmdao_option_name].copy()
        solver_options.update(self.options[openmdao_option_name])
        return solver_options
