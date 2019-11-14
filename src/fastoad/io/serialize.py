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
from typing import TypeVar, IO, List, Sequence

import numpy as np
import openmdao.api as om

from fastoad.openmdao.types import Variable, SystemSubclass

OMFileIOSubclass = TypeVar('OMFileIOSubclass', bound='AbstractOMFileIO')


class AbstractOMFileIO(ABC):
    """
    Base class for reading OpenMDAO variable values.

    Methods :meth:`read_variables` and :meth:`write_variables` have to be implemented
    according to chosen file format.

    :param data_source: the I/O stream used for reading or writing data
    """

    def __init__(self, data_source: IO):
        self._data_source = data_source

    def read(self, only: List[str] = None, ignore: List[str] = None) -> om.IndepVarComp:
        """
        Reads variables from provided data source.

        :param only: List of OpenMDAO variable names that should be read. Other names will be
                     ignored. If None, all variables will be read.
        :param ignore: List of OpenMDAO variable names that should be ignored when reading.
        :return: an IndepVarComp() instance where outputs have been defined using provided source
        """
        variables = self.read_variables()
        used_variables = self._filter_variables(variables, only=only, ignore=ignore)

        ivc = om.IndepVarComp()
        for name, value, units in used_variables:
            ivc.add_output(name, val=np.array(value), units=units)

        return ivc

    def write(self, ivc: om.IndepVarComp, only: List[str] = None, ignore: List[str] = None):
        """
        Writes output variables from provided IndepVarComp instance.

        :param ivc: the IndepVarComp instance
        :param only: List of OpenMDAO variable names that should be written. Other names will be
                     ignored. If None, all variables will be written.
        :param ignore: List of OpenMDAO variable names that should be ignored when writing
        """
        variables = self._get_variables(ivc)
        used_variables = self._filter_variables(variables, only=only, ignore=ignore)
        self.write_variables(used_variables)

    @abstractmethod
    def read_variables(self) -> List[Variable]:
        """
        Reads variables from provided data source file.

        :return: a list of Variable instance
        """

    @abstractmethod
    def write_variables(self, variables: Sequence[Variable]):
        """
        Writes variables to defined data source file.

        :param variables:
       """

    @staticmethod
    def _get_variables(ivc: om.IndepVarComp) -> List[Variable]:
        """ returns the list of variables from provided system """

        variables: List[Variable] = []

        # Outputs are accessible using private member
        # pylint: disable=protected-access
        for (name, value, attributes) in ivc._indep_external:
            variables.append(Variable(name, value, attributes['units']))

        return variables

    @staticmethod
    def _filter_variables(variables: Sequence[Variable], only: Sequence[str] = None,
                          ignore: Sequence[str] = None) -> Sequence[Variable]:
        """
        filters the variables such that the ones in arg only are kept and the ones in
        arg ignore are removed.

        :param variables:
        :param only: List of OpenMDAO variable names that should be written. Other names will be
                     ignored. If None, all variables will be written.
        :param ignore: List of OpenMDAO variable names that should be ignored when writing
        :return: filtered variables
        """
        if only is None:
            used_variables = variables
        else:
            used_variables = [variable for variable in variables if variable.name in only]

        if ignore is not None:
            used_variables = [variable for variable in used_variables
                              if variable.name not in ignore]

        return used_variables
