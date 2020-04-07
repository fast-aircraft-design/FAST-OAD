# -*- coding: utf-8 -*-
"""
  Sellar openMDAO group
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


import abc
from typing import Type

from openmdao.api import Group, IndepVarComp
from openmdao.api import NonlinearBlockGS

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
        """ Provides an instance for discipline 1 """

    @staticmethod
    @abc.abstractmethod
    def create_disc2():
        """ Provides an instance for discipline 2 """

    @staticmethod
    @abc.abstractmethod
    def create_functions():
        """ Provides an instance for functions """


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


class Sellar(Group):
    """ An OpenMDAO base component to encapsulate Sellar MDA """

    def __init__(self, sellar_factory: Type[ISellarFactory] = StandardSellarFactory, **kwargs):
        """

        :param sellar_factory: will provide the components
                    (disciplines 1 and 2 + functions)
        :param thrift_client:
        :param kwargs:
        """
        super(Sellar, self).__init__(**kwargs)

        self._sellar_factory = sellar_factory
        self.nonlinear_solver = NonlinearBlockGS()
        self.nonlinear_solver.options["atol"] = 1.0e-10
        self.nonlinear_solver.options["rtol"] = 1.0e-10
        self.nonlinear_solver.options["maxiter"] = 10
        self.nonlinear_solver.options["err_on_non_converge"] = True
        self.nonlinear_solver.options["iprint"] = 1

    def setup(self):
        indeps = self.add_subsystem("indeps", IndepVarComp(), promotes=["*"])
        indeps.add_output("x", 2)
        indeps.add_output("z", [5, 2])
        self.add_subsystem(
            "Disc1", self._sellar_factory.create_disc1(), promotes=["x", "z", "y1", "y2"]
        )
        self.add_subsystem("Disc2", self._sellar_factory.create_disc2(), promotes=["z", "y1", "y2"])
        self.add_subsystem(
            "Functions",
            self._sellar_factory.create_functions(),
            promotes=["x", "z", "y1", "y2", "f", "g1", "g2"],
        )
