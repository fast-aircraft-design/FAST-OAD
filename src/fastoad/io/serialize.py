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
from fnmatch import fnmatchcase
from typing import TypeVar, IO, List, Sequence

import numpy as np
import openmdao.api as om
from fastoad.openmdao.variables import Variables

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

        Elements of `only` and `ignore` can be real variable names or Unix-shell-style patterns.
        In any case, comparison is case-sensitive.

        :param only: List of OpenMDAO variable names that should be read. Other names will be
                     ignored. If None, all variables will be read.
        :param ignore: List of OpenMDAO variable names that should be ignored when reading.
        :return: an IndepVarComp() instance where outputs have been defined using provided source
        """
        variables = self.read_variables()
        used_variables = self._filter_variables(variables, only=only, ignore=ignore)

        ivc = om.IndepVarComp()
        for var_name, metadata in used_variables.items():
            ivc.add_output(var_name, val=np.array(metadata['value']), units=metadata['units'])

        return ivc

    def write(self, ivc: om.IndepVarComp, only: List[str] = None, ignore: List[str] = None):
        """
        Writes output variables from provided IndepVarComp instance.

        Elements of `only` and `ignore` can be real variable names or Unix-shell-style patterns.
        In any case, comparison is case-sensitive.

        :param ivc: the IndepVarComp instance
        :param only: List of OpenMDAO variable names that should be written. Other names will be
                     ignored. If None, all variables will be written.
        :param ignore: List of OpenMDAO variable names that should be ignored when writing
        """
        variables = self._get_variables(ivc)
        used_variables = self._filter_variables(variables, only=only, ignore=ignore)
        self.write_variables(used_variables)

    @abstractmethod
    def read_variables(self) -> Variables:
        """
        Reads variables from provided data source file.

        :return: a list of Variable instance
        """

    @abstractmethod
    def write_variables(self, variables: Variables):
        """
        Writes variables to defined data source file.

        :param variables:
       """

    def _get_variables(self, ivc: om.IndepVarComp) -> Variables:
        """ returns the list of variables from provided system """

        variables = Variables()

        # Outputs are accessible using private member
        # pylint: disable=protected-access
        for (name, value, attributes) in ivc._indep_external:
            metadata = {'value': value}
            metadata.update(attributes)
            variables[name] = metadata

        return variables

    @staticmethod
    def _filter_variables(variables: Variables, only: Sequence[str] = None,
                          ignore: Sequence[str] = None) -> Variables:
        """
        filters the variables such that the ones in arg only are kept and the ones in
        arg ignore are removed.

        Elements of `only` and `ignore` can be variable names or Unix-shell-style patterns.
        In any case, filter is case-sensitive.

        :param variables:
        :param only: List of OpenMDAO variable names that should be written. Other names will be
                     ignored. If None, all variables will be written.
        :param ignore: List of OpenMDAO variable names that should be ignored when writing
        :return: filtered variables
        """

        # Dev not: We use sets, but sets of Variable instances (namedtuples with a list as item) do
        # not work. Do we work with variable names instead.

        var_names = variables.keys()

        if only is None:
            used_var_names = set(var_names)
        else:
            used_var_names = set()
            for pattern in only:
                used_var_names.update(
                    [variable_name for variable_name in variables if
                     fnmatchcase(variable_name, pattern)])

        if ignore is not None:
            for pattern in ignore:
                used_var_names.difference_update(
                    [variable_name for variable_name in variables if
                     fnmatchcase(variable_name, pattern)])

        # It could be simpler, but I want to keep the order
        return Variables(
            {var_name: attributes for var_name, attributes in variables.items() if var_name in used_var_names})
