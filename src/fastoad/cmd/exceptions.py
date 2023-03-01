"""
Exception for cmd package
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
