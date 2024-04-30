"""
Convenience functions for file and directories
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
from pathlib import Path
from typing import Union, overload


@overload
def as_path(path: None) -> None:
    ...


@overload
def as_path(path: Union[str, PathLike]) -> Path:
    ...


def as_path(path):
    """
    :param path:
    :return: `path` itself if `path` is a Path,
             or a Path object from `path` if possible,
             or None otherwise.
    """
    if isinstance(path, Path):
        return path

    try:
        return Path(path)
    except TypeError:
        return None


def make_parent_dir(path: Union[str, PathLike]):
    """Ensures parent directory of provided path exists or is created"""
    as_path(path).parent.mkdir(parents=True, exist_ok=True)
