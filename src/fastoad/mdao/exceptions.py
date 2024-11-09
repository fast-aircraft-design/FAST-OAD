"""
Module for custom Exception classes linked to OpenMDAO
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
