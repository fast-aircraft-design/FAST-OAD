"""
Module for managing OpenMDAO variables
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
from typing import Dict


class Variable:
    """
    A class for storing data of OpenMDAO variables
    """

    def __init__(self, name, value, units):
        self.name: str = name
        """ Name of the variable """

        self.value = value
        """ Value of the variable"""

        self.attributes: Dict = {'units': units}
        """ Other attributes of the variable """

    @property
    def units(self):
        """ units associated to value """
        return self.attributes['units']

    def __eq__(self, other):
        return (self.name == other.name and
                self.value == other.value and
                self.attributes == other.attributes)

    def __repr__(self):
        return 'Variable(name=%s, value=%s, units=%s)' % (self.name, self.value, self.units)
