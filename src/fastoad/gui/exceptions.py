"""
Exception for GUI
"""

from fastoad.exceptions import FastError


class FastMissingFile(FastError):
    """Raised when a file does not exist"""
