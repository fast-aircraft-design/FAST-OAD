"""
Tests around ImplicitComponent and Newton solver (from issue #431).
These tests detect problems about doing deepcopy of a Problem that contains not pickle-able objects.
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

import openmdao.api as om

from fastoad._utils.testing import run_system
from ..problem import FASTOADProblem


class QuadraticComp(om.ImplicitComponent):
    """
    A Simple Implicit Component representing a Quadratic Equation.

    R(a, b, c, x) = ax^2 + bx + c

    Solution via Quadratic Formula:
    x = (-b + sqrt(b^2 - 4ac)) / 2a
    """

    def setup(self):
        self.add_input("a", val=1.0)
        self.add_input("b", val=-4.0)
        self.add_input("c", val=3.0)
        self.add_output("x", val=6.0)

    def setup_partials(self):
        self.declare_partials(of="x", wrt="*")

    def apply_nonlinear(self, inputs, outputs, residuals):
        a = inputs["a"]
        b = inputs["b"]
        c = inputs["c"]
        x = outputs["x"]
        residuals["x"] = a * x ** 2 + b * x + c

    def solve_nonlinear(self, inputs, outputs):
        a = inputs["a"]
        b = inputs["b"]
        c = inputs["c"]
        outputs["x"] = (-b + (b ** 2 - 4 * a * c) ** 0.5) / (2 * a)

    def linearize(self, inputs, outputs, partials):
        a = inputs["a"]
        b = inputs["b"]
        x = outputs["x"]

        partials["x", "a"] = x ** 2
        partials["x", "b"] = x
        partials["x", "c"] = 1.0
        partials["x", "x"] = 2 * a * x + b

        self.inv_jac = 1.0 / (2 * a * x + b)


def test_implicit_component_openmdao():

    p = om.Problem()

    p.model.add_subsystem("ivc_a", om.IndepVarComp("a", val=1.0), promotes=["*"])
    p.model.add_subsystem("ivc_b", om.IndepVarComp("b", val=-4.0), promotes=["*"])
    p.model.add_subsystem("ivc_c", om.IndepVarComp("c", val=3.0), promotes=["*"])
    p.model.add_subsystem("quad", QuadraticComp(), promotes=["*"])

    p.model.nonlinear_solver = om.NewtonSolver(solve_subsystems=False)
    p.model.linear_solver = om.DirectSolver()

    p.setup()

    p.run_model()

    # sanity check: should sum to 3
    print(p["quad.x"])


def test_implicit_component_fast_oad():

    p = FASTOADProblem()

    p.model.add_subsystem("ivc_a", om.IndepVarComp("a", val=1.0), promotes=["*"])
    p.model.add_subsystem("ivc_b", om.IndepVarComp("b", val=-4.0), promotes=["*"])
    p.model.add_subsystem("ivc_c", om.IndepVarComp("c", val=3.0), promotes=["*"])
    p.model.add_subsystem("quad", QuadraticComp(), promotes=["*"])

    p.model.nonlinear_solver = om.NewtonSolver(solve_subsystems=False)
    p.model.linear_solver = om.DirectSolver()

    p.setup()

    p.run_model()

    # sanity check: should sum to 3
    print(p["quad.x"])


def test_implicit_component_fast_oad_no_newton():

    p = FASTOADProblem()

    p.model.add_subsystem("ivc_a", om.IndepVarComp("a", val=1.0), promotes=["*"])
    p.model.add_subsystem("ivc_b", om.IndepVarComp("b", val=-4.0), promotes=["*"])
    p.model.add_subsystem("ivc_c", om.IndepVarComp("c", val=3.0), promotes=["*"])
    p.model.add_subsystem("quad", QuadraticComp(), promotes=["*"])

    p.model.nonlinear_solver = om.NonlinearBlockGS()
    p.model.linear_solver = om.DirectSolver()

    p.setup()

    p.run_model()

    # sanity check: should sum to 3
    print(p["quad.x"])


def test_implicit_component_fast_oad_run_system():

    ivc = om.IndepVarComp()
    ivc.add_output(name="a", val=1.0)
    ivc.add_output(name="b", val=-4.0)
    ivc.add_output(name="c", val=3.0)

    p = run_system(QuadraticComp(), ivc)

    # sanity check: should sum to 3
    print(p["x"])

    # This one is gonna work because the run_system function uses an OpenMDAO problem and not a
    # FASTOADProblem
    p_2 = run_system(QuadraticComp(), ivc, add_solvers=True)

    # sanity check: should sum to 3
    print(p_2["x"])
