"""Exceptions for io.xml module"""

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
