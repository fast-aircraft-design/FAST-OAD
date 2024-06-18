"""
Convenience classes to be used in OpenMDAO components.
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


import abc

import openmdao.api as om


class CycleGroup(om.Group, abc.ABC):
    """
    Use this class as a base class if your model should contain solvers.

    This class defines standard options to control inner solvers.

    Please be sure to call the `super()` method when using initialize() and setup()
    in the derived class.

    By default, the inner solver is activated. If you want your subclass to deactivate
    the solver by default, you can define it when subclassing::

        class MyGroup(CycleGroup, use_solver_by_default=False):
            ...


    You may also specify default solver settings for your subclass. They will be used
    when adding the solver, unless overwritten through OpenMDAO options when instantiating::

        class MyGroup(
            CycleGroup,
            default_linear_solver="om.ScipyKrylov",
            default_nonlinear_solver="om.NewtonSolver",
            default_nonlinear_options={"maxiter": 50, "iprint": 0},
            default_linear_options={"maxiter": 100, "rtol": 1.e-6},
        ):
            ...

    """

    def __init_subclass__(
        cls,
        use_solvers_by_default: bool = True,
        default_linear_solver: str = "om.DirectSolver",
        default_nonlinear_solver: str = "om.NonlinearBlockGS",
        default_linear_options: dict = None,
        default_nonlinear_options: dict = None,
    ):
        cls.use_solvers_by_default = use_solvers_by_default
        cls.default_linear_solver = default_linear_solver
        cls.default_nonlinear_solver = default_nonlinear_solver
        cls.default_solver_options = {
            "linear_solver_options": default_linear_options if default_linear_options else {},
            "nonlinear_solver_options": default_nonlinear_options
            if default_nonlinear_options
            else {},
        }

    def initialize(self):
        super().initialize()
        self.options.declare(
            "use_inner_solvers",
            types=bool,
            default=self.use_solvers_by_default,
            desc="If True, solvers are added to the group. The solver classes are decided "
            'by options "linear_solver" and "nonlinear_solver". '
            "If False, no solver is added and other solver-related options have no effect.",
        )
        self.options.declare(
            "use_inner_solver",
            types=bool,
            default=self.use_solvers_by_default,
            deprecation=(
                '"use_inner_solver" option is deprecated. Please use "use_inner_solvers" option',
                "use_inner_solvers",
            ),
        )
        self.options.declare(
            "linear_solver",
            types=(bool, str),
            default=self.default_linear_solver,
            desc="If a string is given like `om.LinearBlockGS`, it will be used "
            "(convention `import openmdao.api as om' is assumed`. "
            "If `False` is given, no linear solver is added (i.e. om.LinearRunOnce is used). "
            'Ignored if option "use_inner_solver" is False',
            check_valid=_forbid_true_value,
        )
        self.options.declare(
            "nonlinear_solver",
            types=(bool, str),
            default=self.default_nonlinear_solver,
            desc="If a string is given like `om.NewtonSolver`, it will be used "
            "(convention `import openmdao.api as om' is assumed`. "
            "If `False` is given, no non-linear solver is added (i.e. om.NonlinearRunOnce is used)."
            'Ignored if option "use_inner_solver" is False',
            check_valid=_forbid_true_value,
        )
        self.options.declare(
            "linear_solver_options",
            types=dict,
            default=self.default_solver_options["linear_solver_options"],
            desc="Options for linear solver. This dict will be updated with provided dict, "
            "meaning that options that are not in provided dict will keep the default value. "
            'Ignored if "use_inner_solver" is False.',
        )
        self.options.declare(
            "nonlinear_solver_options",
            types=dict,
            default=self.default_solver_options["nonlinear_solver_options"],
            desc="Options for non-linear solver. This dict will be updated with provided dict, "
            "meaning that options that are not in provided dict will keep the default value. "
            'Ignored if "use_inner_solver" is False.',
        )

    def setup(self):
        super().setup()

        if self.options["use_inner_solvers"]:
            linear_solver_class = self._get_solver_class("linear_solver")
            nonlinear_solver_class = self._get_solver_class("nonlinear_solver")

            linear_solver_options = self._get_solver_options("linear_solver_options")
            nonlinear_solver_options = self._get_solver_options("nonlinear_solver_options")

            if linear_solver_class:
                self.linear_solver = linear_solver_class(**linear_solver_options)
            if nonlinear_solver_class:
                self.nonlinear_solver = nonlinear_solver_class(**nonlinear_solver_options)

    def _get_solver_class(self, option_name: str):
        """
        For option_name in ["linear_solver", "nonlinear_solver"], provide the solver class
        from the string self.options[option_name].
        Class will be om.<class_name>, whether the stringbegins with "om." or not.
        """
        solver_name = self.options[option_name]
        if isinstance(solver_name, str):
            if solver_name.startswith("om."):
                solver_name = solver_name[3:]
            solver_class = om.__dict__[solver_name]
        else:
            # Option has been set to False
            solver_class = None
        return solver_class

    def _get_solver_options(self, openmdao_option_name: str):
        # default dict of solver options is updated with user-provided solver options.
        solver_options = self.default_solver_options[openmdao_option_name].copy()
        solver_options.update(self.options[openmdao_option_name])
        return solver_options


def _forbid_true_value(name, value):
    """
    For using in check_valid with options "linear_solver" and "nonlinear_solver".

    False is authorized to deactivate the solver, but True is not needed and could
    lead to misunderstanding (what if "use_inner_solvers==False" but "linear_solver==True" ?)
    """
    if value is True:
        other_solver_kind = "nonlinear_solver" if name == "linear_solver" else "linear_solver"
        raise ValueError(
            f'`True` value is not accepted for option "{name}". '
            f'Please use "use_inner_solvers=True" to activate both linear and non-linear solvers. '
            f'If you want to activate only "{name}", please use "use_inner_solvers=True" '
            f'and "{other_solver_kind}=False".'
        )


class BaseCycleGroup(CycleGroup):
    """
    Inherited from :class:`CycleGroup` with no modification of default behavior.
    """
