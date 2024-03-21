"""
This module provides a standard Sellar problem.

It is intended as a basis for all Sellar-based tests.
SellarModel and SellarProblem should be used as-is.
Providing different implementations of ISellarFactory will allow to provide
the problem components in various ways
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
from dataclasses import dataclass

import openmdao.api as om

from .disc1 import BasicDisc1
from .disc2 import BasicDisc2
from .function_f import BasicFunctionF
from .functions_g import BasicFunctionG1, BasicFunctionG2


class ISellarFactory(abc.ABC):
    """
    The interface for providing Sellar components. Is used by SellarModel()
    """

    @abc.abstractmethod
    def create_disc1(self):
        """
        Provides an instance for discipline 1 OpenMDAO component.

        Component inputs:
          - x
          - z (2 elements)
          - y2
        Component output:
          - y1
        """

    @abc.abstractmethod
    def create_disc2(self):
        """
        Provides an instance for discipline 2 OpenMDAO component.

        Component inputs:
          - z (2 elements)
          - y1
        Component output:
          - y2
        """

    @abc.abstractmethod
    def create_objective_function(self):
        """
        Provides an instance for objective function OpenMDAO component.

        Component inputs:
          - x
          - z (2 elements)
          - y1
          - y2
        Component output:
          - f
        """

    @abc.abstractmethod
    def create_constraints(self):
        """
        Provides an instance for constraints OpenMDAO component.

        Component inputs:
          - y1
          - y2
        Component outputs:
          - g1
          - g2
        """


@dataclass
class GenericSellarFactory(ISellarFactory):
    """
    Provides components through standard Python import
    """

    disc1_class: type = BasicDisc1
    disc2_class: type = BasicDisc2
    f_class: type = BasicFunctionF
    g1_class: type = BasicFunctionG1
    g2_class: type = BasicFunctionG2

    def create_disc1(self):
        return self.disc1_class()

    def create_disc2(self):
        return self.disc2_class()

    def create_objective_function(self):
        return self.f_class()

    def create_constraints(self):
        constraints = om.Group()
        constraints.add_subsystem("function_g1", self.g1_class(), promotes=["*"])
        constraints.add_subsystem("function_g2", self.g2_class(), promotes=["*"])

        return constraints


class BasicSellarModel(om.Group):
    """An OpenMDAO base component to encapsulate Sellar MDA"""

    def initialize(self):
        self.options.declare("sellar_factory", default=GenericSellarFactory())

        self.nonlinear_solver = om.NonlinearBlockGS()
        self.nonlinear_solver.options["atol"] = 1.0e-10
        self.nonlinear_solver.options["rtol"] = 1.0e-10
        self.nonlinear_solver.options["maxiter"] = 10
        self.nonlinear_solver.options["err_on_non_converge"] = True
        self.nonlinear_solver.options["iprint"] = 1

    def setup(self):
        sellar_factory: ISellarFactory = self.options["sellar_factory"]
        indeps = self.add_subsystem("indeps", om.IndepVarComp(), promotes=["*"])
        indeps.add_output("x", 2)
        indeps.add_output("z", [5, 2])
        self.add_subsystem("disc1", sellar_factory.create_disc1(), promotes=["*"])
        self.add_subsystem("disc2", sellar_factory.create_disc2(), promotes=["*"])
        self.add_subsystem("objective", sellar_factory.create_objective_function(), promotes=["*"])
        self.add_subsystem("constraints", sellar_factory.create_constraints(), promotes=["*"])


class BasicSellarProblem(om.Problem):
    """
    Base settings for Sellar optimization.

    The Sellar model has to be manually set, though.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.driver = om.ScipyOptimizeDriver()
        self.driver.options["optimizer"] = "SLSQP"
        self.driver.options["maxiter"] = 100
        self.driver.options["tol"] = 1e-8

        self.model.add_design_var("x", lower=0, upper=10)
        self.model.add_design_var("z", lower=0, upper=10)
        self.model.add_objective("f")
        self.model.add_constraint("g1", upper=0)
        self.model.add_constraint("g2", upper=0)
