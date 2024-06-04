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

from fnmatch import fnmatchcase
from os import PathLike
from pathlib import Path
from typing import List, Sequence, Union, IO, Optional

from fastoad.openmdao.variables import VariableList
from . import IVariableIOFormatter
from .xml import VariableXmlStandardFormatter
from .._utils.files import as_path
from ..exceptions import FastError


class VariableIO:
    """
    Class for reading and writing variable values from/to file.

    The file format is defined by the class provided as `formatter` argument.

    :param data_source: I/O stream, or file path, used for reading or writing data
    :param formatter: a class that determines the file format to be used. Defaults to a
                      VariableBasicXmlFormatter instance.
    """

    def __init__(
        self,
        data_source: Optional[Union[str, PathLike, IO]],
        formatter: IVariableIOFormatter = None,
    ):
        if isinstance(data_source, (str, PathLike)):
            data_source = as_path(data_source)

        #: I/O stream, or file path, used for reading or writing data
        self.data_source = data_source

        self.formatter = formatter

    @property
    def formatter(self) -> IVariableIOFormatter:
        """Class that determines the file format to be used."""
        return self._formatter

    @formatter.setter
    def formatter(self, formatter: IVariableIOFormatter):
        self._formatter = formatter if formatter else VariableXmlStandardFormatter()

    def read(self, only: List[str] = None, ignore: List[str] = None) -> Optional[VariableList]:
        """
        Reads variables from provided data source.

        Elements of `only` and `ignore` can be real variable names or Unix-shell-style patterns.
        In any case, comparison is case-sensitive.

        :param only: List of variable names that should be read. Other names will be
                     ignored. If None, all variables will be read.
        :param ignore: List of variable names that should be ignored when reading.
        :return: a VariableList instance where outputs have been defined using provided source.
        """
        if isinstance(self.data_source, Path) and not self.data_source.is_file():
            raise FileNotFoundError(
                f'File "{self.data_source}" is unavailable for reading.'
            ) from FastError()

        variables = self.formatter.read_variables(self.data_source)
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

        # Before writing, variables are sorted to have short paths first. With equal path length
        # alphanumeric order will be used.
        used_variables.sort(key=lambda var: "%02i_%s" % (len(var.name.split(":")), var.name))

        self.formatter.write_variables(self.data_source, used_variables)

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

        if only is None and ignore is None:
            return variables

        used_variables = VariableList(
            [
                variable
                for variable in variables
                if not ignore or not any(fnmatchcase(variable.name, pattern) for pattern in ignore)
            ]
        )

        if only is not None:
            used_variables = VariableList(
                [
                    variable
                    for variable in used_variables
                    if any(fnmatchcase(variable.name, pattern) for pattern in only)
                ]
            )

        return used_variables


class DataFile(VariableList):
    """
    Class for managing FAST-OAD data files.

    Behaves like :class:`~fastoad.openmdao.variables.VariableList` class but has :meth:`load` and
    :meth:`save` methods.
    """

    def __init__(
        self,
        data_source: Union[str, PathLike, IO, list] = None,
        formatter: IVariableIOFormatter = None,
        load_data=True,
    ):
        """
        If variable list is specified for data_source, :attr:`file_path` will have to be set before
        using :method:`save`.

        :param data_source: Can be the file path where data will be loaded and saved, or a list of
                            :class:`~fastoad.openmdao.variables.Variable` instances that will
                            be used for initialization (or a
                            :class:`~fastoad.openmdao.variables.VariableList` instance).
        :param formatter: (ignored if data_source is not an I/O stream nor a file path)
                          a class that determines the file format to be used. Defaults to FAST-OAD
                          native format. See :class:`VariableIO` for more information.
        :param load_data: (ignored if data_source is not an I/O stream nor a file path)
                          if True, file is expected to exist and its content will be loaded at
                          instantiation.
        """
        super().__init__()

        self._variable_io = None
        self.formatter = formatter

        if isinstance(data_source, list):
            self.update(data_source)
        elif data_source is not None:
            self.file_path = data_source
            if load_data:
                self.load()

    @property
    def file_path(self) -> str:
        """Path of data file."""
        return self._variable_io.data_source if self._variable_io else None

    @file_path.setter
    def file_path(self, value: str):
        self._variable_io = VariableIO(value, self.formatter)

    @property
    def formatter(self) -> IVariableIOFormatter:
        """Class that defines the file format."""
        if self._variable_io:
            self._formatter = self._variable_io.formatter
        return self._formatter

    @formatter.setter
    def formatter(self, value: IVariableIOFormatter):
        self._formatter = value
        if self._variable_io:
            self._variable_io.formatter = value

    def load(self):
        """Loads file content."""
        self.clear()
        self.update(self._variable_io.read(), add_variables=True)

    def save(self):
        """Saves current state of variables in file."""
        if self.file_path is None:
            raise FileNotFoundError(
                "Destination file not set. Please use .save_as() instead."
            ) from FastError()
        self._variable_io.write(self)

    def save_as(
        self,
        file_path: Union[str, PathLike],
        overwrite=False,
        formatter: IVariableIOFormatter = None,
    ):
        """
        Sets the associated file path as specified and saves current state of variables.

        :param file_path:
        :param overwrite: if specified file already exists and overwrite is False, an error is
                          triggered.
        :param formatter: a class that determines the file format to be used. Defaults to FAST-OAD
                          native format. See :class:`VariableIO` for more information.
        """
        file_path = as_path(file_path)
        if not overwrite and file_path.exists():
            raise FileExistsError(f'File "{file_path}" already exists.') from FastError()

        self._variable_io = VariableIO(file_path, formatter)

        self.save()
