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

class VarXpathTranslator:

    def __init__(self):
        self._var_names = []
        self._xpaths = []

    def set(self, var_names, xpaths):
        if len(var_names) != len(xpaths):
            raise IndexError('lists var_names and xpaths should have same length (%i and %i)' %
                             (len(var_names), len(xpaths)))
        self._var_names = var_names
        self._xpaths = xpaths

    @property
    def variable_names(self):
        return self._var_names

    @property
    def xpaths(self):
        return self._xpaths

    def get_xpath(self, var_name):
        if var_name in self._var_names:
            i = self._var_names.index(var_name)
            return self._xpaths[i]
        return None

    def get_variable_name(self, xpath):
        if xpath in self._xpaths:
            i = self._xpaths.index(xpath)
            return self._var_names[i]
        return None
