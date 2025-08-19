"""
Module for custom Exception classes
"""


class FastError(Exception):
    """
    Base Class for exceptions related to the FAST framework.
    """


class NoSetupError(FastError):
    """
    No Setup Error.

    This exception indicates that a setup of the OpenMDAO instance has not been done, but was
    expected to be.
    """


class XMLReadError(FastError):
    """
    XML file read Error.

    This exception indicates that an error occurred when reading an xml file.
    """


class FastUnknownEngineSettingError(FastError):
    """
    Raised when an unknown engine setting code has been encountered
    """


class FastUnexpectedKeywordArgument(FastError):
    """
    Raised when an instantiation is done with an incorrect keyword argument.
    """

    def __init__(self, bad_keyword):
        super().__init__("Unexpected keyword argument: %s" % bad_keyword)
        self.bad_keyword = bad_keyword
