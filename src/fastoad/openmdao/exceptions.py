"""
Module for custom Exception classes linked to OpenMDAO
"""

from os import PathLike
from typing import Iterable

from fastoad._utils.files import as_path
from fastoad.exceptions import FastError


class FASTNanInInputsError(FastError):
    """Raised if NaN values are read in input data file."""

    def __init__(self, input_file_path: [str, PathLike], nan_variable_names: Iterable[str]):
        self.input_file_path = as_path(input_file_path)
        self.nan_variable_names = sorted(list(nan_variable_names))

        msg = (
            f"NaN values found in inputs. Please check that {input_file_path} contains "
            f"following variables and that they are not NaN: {self.nan_variable_names}"
        )

        super().__init__(self, msg)
