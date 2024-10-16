"""Checks about packages and resources"""

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

from importlib.resources import files, as_file
from os import PathLike
from types import ModuleType
from typing import List, TextIO, Union


class PackageReader:
    """
    Wrapper of `importlib.resources.files` which handles when `package_name` is
    not a package or does not exist.

    It also offers a replacement for some old attributes of importlib.resources.

    :param package_name: Name of package to inspect.
    """

    def __init__(self, package_name: Union[str, ModuleType]):
        """
        :param package_name:
        """
        self.is_package = False
        self.exists = True
        self.is_module = False
        self.has_error = False
        self._contents: List[str] = []
        self.package_name = package_name

    @property
    def package_name(self):
        """Name of package to inspect."""
        return self._package_name

    @package_name.setter
    def package_name(self, package_name: str):
        self._package_name = package_name
        if package_name:
            try:
                self._check_package_content(package_name)
            except (ModuleNotFoundError, TypeError):
                # Either the indicated package does not exist, or it is a file with no extension.
                # We want to ensure existence to correctly set self.exists.
                if "." in package_name:
                    parent_package_name, module_name = package_name.rsplit(".", 1)
                    parent_package = PackageReader(parent_package_name)
                    if parent_package.is_package and module_name + ".py" in parent_package.contents:
                        self.exists = True
                        self.is_module = True
                else:
                    # Here we assume non-existence
                    self.exists = False
            except Exception:  # pylint: disable = W0703
                # Here we catch any Python error that may happen when reading the loaded code.
                # Thus, we ensure to not break the application if a module is incorrectly written.
                self.has_error = True

    @property
    def contents(self) -> List[str]:
        """
        The list.
        """
        return self._contents

    def is_resource(self, name: str):
        """
        Replaces legacy importlib.resources.is_resource().

        True if `name` is a resource inside `package`.

        Directories are *not* resources.
        """
        return files(self.package_name).joinpath(name).is_file()

    def open_text(
        self,
        resource: Union[str, PathLike],
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> TextIO:
        """
        Replaces legacy importlib.resources.open_text().

        :return: a file-like object opened for text reading of the resource
        """
        return (files(self.package_name) / str(resource)).open(
            "r",
            encoding=encoding,
            errors=errors,
        )

    def path(self, resource: Union[str, PathLike]):
        """
        Replaces legacy importlib.resources.path().

        A context manager providing a file path object to the resource.

        If the resource does not already exist on its own on the file system,
        a temporary file will be created. If the file was created, the file
        will be deleted upon exiting the context manager (no exception is
        raised if the file was deleted prior to the context manager
        exiting).

        """
        return as_file(files(self.package_name).joinpath(resource))

    def _check_package_content(self, package_name: str):
        """
        Sets attributes self._contents, self.is_package and self.is_module.
        """

        traversable = files(package_name)
        # If package_name matches a module (i.e. a .py file),
        # importlib.resources.files() returns the path to the parent directory.
        # Then we check if the result with parent package is the same.
        parent_package_name = ".".join(package_name.split(".")[:-1])
        parent_traversable = files(parent_package_name) if parent_package_name else None
        if traversable == parent_traversable:
            self.is_module = True
        else:
            self._contents = [resource.name for resource in traversable.iterdir()]
            self.is_package = True
