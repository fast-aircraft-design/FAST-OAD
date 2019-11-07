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
from typing import TypeVar, IO, List

import openmdao.api as om

OMFileIOSubclass = TypeVar('OMFileIOSubclass', bound='AbstractOMFileIO')


class AbstractOMFileIO(ABC):
    """
    Interfaces for reading OpenMDAO variable values
    """

    def __init__(self, data_source: IO):
        self._data_source = data_source

    @abstractmethod
    def read(self, only: List[str] = None, ignore: List[str] = None) -> om.IndepVarComp:
        """
        Reads variables from provided data source.

        :param only: List of OpenMDAO variable names that should be read. Other names will be
                     ignored. If None, all variables will be read.
        :param ignore: List of OpenMDAO variable names that should be ignored when reading.
        :return: an IndepVarComp() instance where outputs have been defined using provided source
        """

    @abstractmethod
    def write(self, only: List[str] = None, ignore: List[str] = None):
        """
        Writes output variables from provided IndepVarComp instance.

        :param only: List of OpenMDAO variable names that should be written. Other names will be
                     ignored. If None, all variables will be written.
        :param ignore: List of OpenMDAO variable names that should be ignored when writing
        """
