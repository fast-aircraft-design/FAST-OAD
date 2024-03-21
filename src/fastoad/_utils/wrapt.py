"""
Utilities for usage of wrapt.
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

import copy

import wrapt


class CopyableFunctionWrapper(wrapt.FunctionWrapper):
    """
    A wrapt.FunctionWrapper that is compatible with (deep)copy.
    """

    def __copy__(self):
        return type(self)(copy.copy(self.__wrapped__), self._self_wrapper, self._self_enabled)

    def __deepcopy__(self, memo=None):
        return type(self)(
            copy.deepcopy(self.__wrapped__, memo), self._self_wrapper, self._self_enabled
        )
