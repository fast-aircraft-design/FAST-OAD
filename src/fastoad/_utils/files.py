"""
Convenience functions for file and directories
"""

from os import PathLike
from pathlib import Path
from typing import Union, overload


@overload
def as_path(path: None) -> None: ...


@overload
def as_path(path: Union[str, PathLike]) -> Path: ...


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
