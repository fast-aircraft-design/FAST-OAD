"""
Exception for cmd package
"""

from fastoad.exceptions import FastError


class FastPathExistsError(FastError):
    """Raised when asked for writing a file/folder that already exists."""

    def __init__(self, *args):
        super().__init__(*args)
        self.file_path = args[1]


class FastNoAvailableNotebookError(FastError):
    """Raised when no notebook is available for creation."""

    def __init__(self, distribution_name=None):
        msg = "No notebook available "
        if distribution_name:
            msg += f'in installed package "{distribution_name}".'
        else:
            msg += "in FAST-OAD plugins."

        self.distribution_name = distribution_name
        super().__init__(msg)
