"""
Base class for VariableIOFormatter objects.
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

from abc import ABC, abstractmethod
from os import PathLike
from typing import Union, IO

from fastoad.openmdao.variables import VariableList


class IVariableIOFormatter(ABC):
    """
    Interface for formatter classes to be used in VariableIO class.

    The file format is defined by the implementation of this interface.
    """

    @abstractmethod
    def read_variables(self, data_source: Union[str, PathLike, IO]) -> VariableList:
        """
        Reads variables from provided data source file.

        :param data_source:
        :return: a list of Variable instance
        """

    @abstractmethod
    def write_variables(self, data_source: Union[str, PathLike, IO], variables: VariableList):
        """
        Writes variables to defined data source file.

        :param data_source:
        :param variables:
        """
