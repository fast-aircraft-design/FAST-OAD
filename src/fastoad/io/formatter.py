"""
Base class for VariableIOFormatter objects.
"""

from abc import ABC, abstractmethod
from os import PathLike
from typing import IO, Union

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
