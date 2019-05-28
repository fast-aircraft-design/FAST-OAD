"""
Defines interfaces for reading and writing OpenMDAO variable values
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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
from abc import abstractmethod, ABC
from typing import TypeVar, IO

from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.system import System

SystemSubclass = TypeVar('SystemSubclass', bound=System)


class AbstractOpenMDAOVariableIO(ABC):
    """
    Interfaces for reading OpenMDAO variable values
    """

    def __init__(self, data_source: IO):
        self._data_source = data_source

    @abstractmethod
    def read(self) -> IndepVarComp:
        """

        :return: an IndepVarComp() instance where outputs have been defined using provided source
        """
        pass

    @abstractmethod
    def write(self, system: SystemSubclass):
        """
        Writes output variables from provided system
        """
        pass
