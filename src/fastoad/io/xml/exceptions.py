""" Exceptions for io.xml module """

#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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

from fastoad.exceptions import FastError


class FastXPathEvalError(FastError):
    """
    Raised when some xpath could not be resolved
    """


class FastXpathTranslatorInconsistentLists(FastError):
    """
    Raised when list of variable names and list of XPaths have not the same length
    """


class FastXpathTranslatorDuplicates(FastError):
    """
    Raised when list of variable names or list of XPaths have duplicate entries
    """


class FastXpathTranslatorVariableError(FastError):
    """
    Raised when a variable does not match any xpath in the translator file.
    """

    def __init__(self, variable):
        super().__init__("Unknown variable %s" % variable)
        self.variable = variable


class FastXpathTranslatorXPathError(FastError):
    """
    Raised when a xpath does not match any variable in the translator file.
    """

    def __init__(self, xpath):
        super().__init__("Unknown xpath %s" % xpath)
        self.xpath = xpath


class FastXmlFormatterDuplicateVariableError(FastError):
    """
    Raised a variable is defined more than once in a XML file
    """
