"""Exceptions for mission package."""

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
