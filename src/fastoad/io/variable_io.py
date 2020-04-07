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

from fnmatch import fnmatchcase
from typing import Union, IO, List, Sequence

from fastoad.openmdao.variables import VariableList

from . import IVariableIOFormatter
from .xml import VariableXmlStandardFormatter


class VariableIO:
    """
    Class for reading and writing variable values from/to file.

    The file format is defined by the class provided as `formatter` argument.

    :param data_source: the I/O stream, or a file path, used for reading or writing data
    :param formatter: a class that determines the file format to be used. Defaults to a VariableBasicXmlFormatter
                      instance
    """

    def __init__(self, data_source: Union[str, IO], formatter: IVariableIOFormatter = None):
        self._data_source = data_source
        self.formatter: IVariableIOFormatter = formatter if formatter else VariableXmlStandardFormatter()

    def read(self, only: List[str] = None, ignore: List[str] = None) -> VariableList:
        """
        Reads variables from provided data source.

        Elements of `only` and `ignore` can be real variable names or Unix-shell-style patterns.
        In any case, comparison is case-sensitive.

        :param only: List of variable names that should be read. Other names will be
                     ignored. If None, all variables will be read.
        :param ignore: List of variable names that should be ignored when reading.
        :return: an VariableList instance where outputs have been defined using provided source
        """
        variables = self.formatter.read_variables(self._data_source)
        used_variables = self._filter_variables(variables, only=only, ignore=ignore)
        return used_variables

    def write(self, variables: VariableList, only: List[str] = None, ignore: List[str] = None):
        """
        Writes variables from provided VariableList instance.

        Elements of `only` and `ignore` can be real variable names or Unix-shell-style patterns.
        In any case, comparison is case-sensitive.

        :param variables: a VariableList instance
        :param only: List of variable names that should be written. Other names will be
                     ignored. If None, all variables will be written.
        :param ignore: List of variable names that should be ignored when writing
        """
        used_variables = self._filter_variables(variables, only=only, ignore=ignore)
        self.formatter.write_variables(self._data_source, used_variables)

    @staticmethod
    def _filter_variables(
        variables: VariableList, only: Sequence[str] = None, ignore: Sequence[str] = None
    ) -> VariableList:
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

        # Dev note: We use sets, but sets of Variable instances do
        # not work. Do we work with variable names instead.
        # FIXME: Variable instances are now hashable, so set of Variable instances should now work

        var_names = variables.names()

        if only is None:
            used_var_names = set(var_names)
        else:
            used_var_names = set()
            for pattern in only:
                used_var_names.update(
                    [variable.name for variable in variables if fnmatchcase(variable.name, pattern)]
                )

        if ignore is not None:
            for pattern in ignore:
                used_var_names.difference_update(
                    [variable.name for variable in variables if fnmatchcase(variable.name, pattern)]
                )

        # It could be simpler, but I want to keep the order
        used_variables = VariableList()
        for var in variables:
            if var.name in used_var_names:
                used_variables.append(var)
        return used_variables
