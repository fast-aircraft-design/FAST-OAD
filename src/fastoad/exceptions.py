"""
Module for custom Exception classes
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


class FastError(Exception):
    """
    Base Class for exceptions related to the FAST framework.
    """

    pass

class NoSetupError(FastError):
    """
    No Setup Error.

    This exception indicates that a setup of the OpenMDAO instance has not been done, but was
    expected to be.
    """

    pass
