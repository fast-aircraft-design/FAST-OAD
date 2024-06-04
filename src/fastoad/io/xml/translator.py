"""
Conversion from OpenMDAO variables to XPath
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

from typing import IO, Sequence, Set, Union

import numpy as np

from fastoad.io.xml.exceptions import (
    FastXpathTranslatorDuplicates,
    FastXpathTranslatorInconsistentLists,
    FastXpathTranslatorVariableError,
    FastXpathTranslatorXPathError,
)


class VarXpathTranslator:
    """
    Allows to convert OpenMDAO variable names from and to XPath, using a provided conversion table.

    At instantiation, user can provide (as keyword arguments only):
     - variable_names and xpaths (see :meth:`set`)
     - translation file (see :meth:`read_translation_table`)
    """

    def __init__(
        self,
        *,
        variable_names: Sequence[str] = None,
        xpaths: Sequence[str] = None,
        source: Union[str, IO] = None
    ):
        if variable_names is not None and xpaths is not None:
            self.set(variable_names, xpaths)

        if source is not None:
            self.read_translation_table(source)

    def set(self, variable_names: Sequence[str], xpaths: Sequence[str]):
        """
        Sets the "conversion table", i.e. two lists where each element matches the other with same
        index. Provided lists must have the same length.

        :param variable_names: List of OpenMDAO variable names
        :param xpaths: List of XML Paths
        """
        if len(variable_names) != len(xpaths):
            raise FastXpathTranslatorInconsistentLists(
                "lists var_names and xpaths have not the same length (%i and %i)"
                % (len(variable_names), len(xpaths))
            )

        # check duplicate variable names
        dupe_vars = self._get_duplicates(variable_names)
        if dupe_vars:
            raise FastXpathTranslatorDuplicates(
                "Following variable names are provided more than once: %s" % dupe_vars, dupe_vars
            )

        # check duplicate XPaths
        dupe_xpaths = self._get_duplicates(xpaths)
        if dupe_xpaths:
            raise FastXpathTranslatorDuplicates(
                "Following variable names are provided more than once: %s" % dupe_xpaths,
                dupe_xpaths,
            )

        self._variable_names = list(variable_names)
        self._xpaths = list(xpaths)

    def read_translation_table(self, source: Union[str, IO]):
        """
        Reads a file that sets how OpenMDAO variable are matched to XML Path.
        Provided file should have 2 comma-separated columns:
         - first one with OpenMDAO names
         - second one with their matching XPath

        :param source:
        """

        arr = np.genfromtxt(source, dtype=str, delimiter=",", autostrip=True)
        self.set(arr[:, 0], arr[:, 1])

    @property
    def variable_names(self) -> Sequence[str]:
        """List of variable names as set in :meth:`set`"""
        return self._variable_names

    @property
    def xpaths(self) -> Sequence[str]:
        """List of XPaths as set in :meth:`set`"""
        return self._xpaths

    def get_xpath(self, var_name: str) -> str:
        """

        :param var_name: OpenMDAO variable name
        :return: XPath that matches var_name
        :raise FastXpathTranslatorVariableError: if var_name is unknown
        """
        if var_name in self._variable_names:
            i = self._variable_names.index(var_name)
            return self._xpaths[i]
        raise FastXpathTranslatorVariableError(var_name)

    def get_variable_name(self, xpath: str) -> str:
        """

        :param xpath: XML Path
        :return: OpenMDAO variable name that matches xpath
        :raise FastXpathTranslatorXPathError: if xpath is unknown
        """
        if xpath in self._xpaths:
            i = self._xpaths.index(xpath)
            return self._variable_names[i]
        raise FastXpathTranslatorXPathError(xpath)

    @staticmethod
    def _get_duplicates(seq: Sequence) -> Set:
        dupes = set()
        seen = set()
        for elem in seq:
            if elem in seen:
                dupes.add(elem)
            else:
                seen.add(elem)
        return dupes
