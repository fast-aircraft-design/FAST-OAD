"""
Conversion from OpenMDAO variables to XPath
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
from typing import Sequence, Union, IO

import numpy as np


class VarXpathTranslator:
    """
    Allows to convert OpenMDAO variable names from and to XPath, using a provided conversion table.
    """

    def __init__(self):
        self._var_names = []
        self._xpaths = []

    def set(self, var_names: Sequence[str], xpaths: Sequence[str]):
        """
        Sets the "conversion table", i.e. two lists where each element matches the other with same
        index. Provided lists must have the same length.

        :param var_names: List of OpenMDAO variable names
        :param xpaths: List of XML Paths
        """
        if len(var_names) != len(xpaths):
            raise IndexError('lists var_names and xpaths should have same length (%i and %i)' %
                             (len(var_names), len(xpaths)))
        self._var_names = list(var_names)
        self._xpaths = list(xpaths)

    def read_translation_table(self, source: Union[str, IO]):
        """
        Reads a file that sets how OpenMDAO variable are matched to XML Path.
        Provided file should have 2 comma-separated columns:
         - first one with OpenMDAO names
         - second one with their matching XPath

        :param source:
        """

        arr = np.genfromtxt(source, dtype=str, delimiter=',', autostrip=True)
        self.set(arr[:, 0], arr[:, 1])

    @property
    def variable_names(self) -> Sequence[str]:
        """ List of variable names as set in :meth:`set`"""
        return self._var_names

    @property
    def xpaths(self) -> Sequence[str]:
        """ List of XPaths as set in :meth:`set`"""
        return self._xpaths

    def get_xpath(self, var_name: str) -> str:
        """

        :param var_name: OpenMDAO variable name
        :return: XPath that matches var_name
        :raise ValueError: if var_name is unknown
        """
        if var_name in self._var_names:
            i = self._var_names.index(var_name)
            return self._xpaths[i]
        raise ValueError('Unknown variable %s' % var_name)

    def get_variable_name(self, xpath: str) -> str:
        """

        :param xpath: XML Path
        :return: OpenMDAO variable name that matches xpath
        :raise ValueError: if xpath is unknown
       """
        if xpath in self._xpaths:
            i = self._xpaths.index(xpath)
            return self._var_names[i]
        raise ValueError('Unknown xpath %s' % xpath)
