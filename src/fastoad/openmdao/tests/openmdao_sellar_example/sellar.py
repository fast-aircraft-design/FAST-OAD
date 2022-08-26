"""Sellar openMDAO group"""
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


import abc
from typing import Type

import openmdao.api as om

from .disc1 import Disc1
from .disc2 import Disc2
from .functions import Functions


class ISellarFactory(abc.ABC):
    """
    The interface for providing Sellar components. Is used by Sellar()
    """

    @staticmethod
    @abc.abstractmethod
    def create_disc1():
        """Provides an instance for discipline 1"""

    @staticmethod
    @abc.abstractmethod
    def create_disc2():
        """Provides an instance for discipline 2"""

    @staticmethod
    @abc.abstractmethod
    def create_functions():
        """Provides an instance for functions"""


class StandardSellarFactory(ISellarFactory):
    """
    Provides components through standard Python import
    """

    @staticmethod
    def create_disc1():
        return Disc1()

    @staticmethod
    def create_disc2():
        return Disc2()

    @staticmethod
    def create_functions():
        return Functions()


class Sellar(om.Group):
    """An OpenMDAO base component to encapsulate Sellar MDA"""

    def __init__(self, sellar_factory: Type[ISellarFactory] = StandardSellarFactory, **kwargs):
        """

        :param sellar_factory: will provide the components
                    (disciplines 1 and 2 + functions)
        :param kwargs:
        """
        super(Sellar, self).__init__(**kwargs)

        self._sellar_factory = sellar_factory

        # This combination of solvers is specifically chosen because it creates some
        # non-pickle-able object that will cause problems in case of deepcopy (see issue #431)
        self.nonlinear_solver = om.NewtonSolver(solve_subsystems=False, maxiter=50)
        self.linear_solver = om.DirectSolver()

    def setup(self):
        indeps = self.add_subsystem("indeps", om.IndepVarComp(), promotes=["*"])
        indeps.add_output("x", 2)
        self.add_subsystem("Disc1", self._sellar_factory.create_disc1(), promotes=["x", "z", "y2"])
        self.add_subsystem("Disc2", self._sellar_factory.create_disc2(), promotes=["z", "y2"])
        self.add_subsystem(
            "Functions",
            self._sellar_factory.create_functions(),
            promotes=["x", "z", "y2", "f", "g1", "g2"],
        )
        self.connect("Disc1.y1", ["Disc2.y1", "Functions.y1"])  # Need for a non-promoted variable
