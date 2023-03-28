"""Exceptions for mission package."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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

from fastoad.exceptions import FastError, FastUnexpectedKeywordArgument


class FastFlightSegmentUnexpectedKeywordArgument(FastUnexpectedKeywordArgument):
    """
    Raised when a segment is instantiated with an incorrect keyword argument.
    """


class FastFlightPointUnexpectedKeywordArgument(FastUnexpectedKeywordArgument):
    """
    Raised when a FlightPoint is instantiated with an incorrect keyword argument.
    """


class FastFlightSegmentIncompleteFlightPoint(FastError):
    """
    Raised when a segment computation encounters a FlightPoint instance without needed parameters.
    """


class FastUnknownMissionElementError(FastError):
    """Raised when an undeclared element type is requested."""

    def __init__(self, element_type: str):
        self.segment_type = element_type

        msg = f'Element type "{element_type}" has not been declared.'

        super().__init__(self, msg)
