"""
Module for custom Exception classes linked to OpenMDAO
"""


#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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


from typing import List

from fastoad.exceptions import FastError


class FASTOpenMDAONanInInputFile(FastError):
    """Raised if NaN values are read in input data file."""

    def __init__(self, input_file_path: str, nan_variable_names: List[str]):
        self.input_file_path = input_file_path
        self.nan_variable_names = nan_variable_names

        msg = "NaN values found in input file (%s). Please check following variables: %s" % (
            input_file_path,
            nan_variable_names,
        )

        super().__init__(self, msg)
