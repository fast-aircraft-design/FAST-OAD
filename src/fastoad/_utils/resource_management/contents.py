"""Checks about packages and resources"""
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

from importlib.resources import contents
from typing import List


class PackageReader:
    """
    Wrapper of `importlib.resources.contents` which handles when `package_name` is
    not a package or does not exist.

    :param package_name:
    :return: An iterator if package exists, an empty SET {} if it does not exist, and None
             if it is not a package
    """

    package_name: str

    def __init__(self, package_name: str):
        """
        :param package_name:
        """
        self.is_package = False
        self.is_module = False
        self.has_error = False
        self._contents = []

        if package_name:
            try:
                self._contents = list(contents(package_name))
                self.is_package = True
            except TypeError:
                self.is_module = True
            except ModuleNotFoundError:
                pass
            except Exception:
                # Here we catch any Python error that may happen when reading the loaded code.
                # Thus, we ensure to not break the application if a module is incorrectly written.
                self.has_error = True

    @property
    def contents(self) -> List[str]:
        """
        An iterator if package exists, otherwise an empty list.
        """
        return self._contents
