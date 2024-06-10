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

import openmdao.api as om
import pytest

from ..group import CycleGroup


def test_base_cycle_group():
    class Group1(CycleGroup):
        pass

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem("group", Group1())
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.DirectSolver)
    assert isinstance(problem.model.group.nonlinear_solver, om.NonlinearBlockGS)

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem("group", Group1(use_solvers=False))
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.LinearRunOnce)
    assert isinstance(problem.model.group.nonlinear_solver, om.NonlinearRunOnce)

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem(
        "group",
        Group1(
            nonlinear_solver=False,
            linear_options={"iprint": 2},
        ),
    )
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.DirectSolver)
    assert isinstance(problem.model.group.nonlinear_solver, om.NonlinearRunOnce)
    assert problem.model.group.linear_solver.options["iprint"] == 2

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem(
        "group",
        Group1(
            linear_solver=False,
            nonlinear_options={"maxiter": 500, "iprint": 0},
        ),
    )
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.LinearRunOnce)
    assert isinstance(problem.model.group.nonlinear_solver, om.NonlinearBlockGS)
    assert problem.model.group.nonlinear_solver.options["maxiter"] == 500
    assert problem.model.group.nonlinear_solver.options["iprint"] == 0

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem(
        "group",
        Group1(
            linear_solver="om.LinearBlockGS",
            nonlinear_solver="om.BroydenSolver",
            linear_options={"iprint": 0},
            nonlinear_options={"maxiter": 200, "iprint": -1},
        ),
    )
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.LinearBlockGS)
    assert isinstance(problem.model.group.nonlinear_solver, om.BroydenSolver)
    assert problem.model.group.linear_solver.options["iprint"] == 0
    assert problem.model.group.nonlinear_solver.options["maxiter"] == 200
    assert problem.model.group.nonlinear_solver.options["iprint"] == -1


def test_cycle_group_with_no_solver_by_default():
    class Group2(CycleGroup, use_solvers_by_default=False):
        pass

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem("group", Group2())
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.LinearRunOnce)
    assert isinstance(problem.model.group.nonlinear_solver, om.NonlinearRunOnce)

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem(
        "group", Group2(use_solvers=True, nonlinear_options={"maxiter": 100, "iprint": 3})
    )
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.DirectSolver)
    assert isinstance(problem.model.group.nonlinear_solver, om.NonlinearBlockGS)
    assert problem.model.group.nonlinear_solver.options["maxiter"] == 100
    assert problem.model.group.nonlinear_solver.options["iprint"] == 3

    # -------------------------------------------------------------------------
    problem = om.Problem()
    with pytest.raises(ValueError) as err:
        problem.model.add_subsystem("group", Group2(linear_solver=True))
    assert 'please use "use_solvers=True" and "nonlinear_solver=False"' in err.value.args[0]

    with pytest.raises(ValueError) as err:
        problem.model.add_subsystem("group", Group2(nonlinear_solver=True))
    assert 'please use "use_solvers=True" and "linear_solver=False"' in err.value.args[0]


def test_cycle_group_with_default_solver_options():
    class Group3(
        CycleGroup,
        default_linear_solver="om.LinearBlockGS",
        default_nonlinear_solver="om.BroydenSolver",
        default_linear_options={"iprint": 2},
        default_nonlinear_options={"maxiter": 200, "iprint": -1},
    ):
        pass

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem("group", Group3())
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.LinearBlockGS)
    assert isinstance(problem.model.group.nonlinear_solver, om.BroydenSolver)
    assert problem.model.group.linear_solver.options["iprint"] == 2
    assert problem.model.group.nonlinear_solver.options["maxiter"] == 200
    assert problem.model.group.nonlinear_solver.options["iprint"] == -1

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem(
        "group",
        Group3(
            nonlinear_solver="om.NewtonSolver",
            linear_options={"iprint": 0},
            nonlinear_options={"iprint": 1},
        ),
    )
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.LinearBlockGS)
    assert isinstance(problem.model.group.nonlinear_solver, om.NewtonSolver)
    assert problem.model.group.linear_solver.options["iprint"] == 0
    assert problem.model.group.nonlinear_solver.options["maxiter"] == 200
    assert problem.model.group.nonlinear_solver.options["iprint"] == 1

    # -------------------------------------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem(
        "group",
        Group3(
            linear_solver="om.DirectSolver",
            nonlinear_solver=False,
            linear_options={"iprint": 3},
        ),
    )
    problem.setup()

    assert isinstance(problem.model.group.linear_solver, om.DirectSolver)
    assert isinstance(problem.model.group.nonlinear_solver, om.NonlinearRunOnce)
    assert problem.model.group.linear_solver.options["iprint"] == 3
